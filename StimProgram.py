#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Program for presenting visual stimuli to patch clamped retinal neurons"
"""

from psychopy import visual, logging, core, event, filters, monitors
from psychopy.tools.coordinatetools import pol2cart
from random import Random
from time import strftime, localtime
from igor import binarywave, packed
import scipy
import numpy
import pprint
import re
import sys
import os
import json
import copy
import ConfigParser

try:
    import u3
    has_u3 = True
except ImportError:
    has_u3 = False

# to make scrolling through recursion errors easier
# sys.setrecursionlimit(100)

__author__ = "Alexander Tomlinson"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "tomlinsa@ohsu.edu"
__status__ = "Prototype"

# suppress extra warnings
# logging.console.setLevel(logging.CRITICAL)

config = ConfigParser.ConfigParser()
config.read('./psychopy/config.ini')


class StimInfo(object):
    """
    class for storing stim info, instantiated in list_of_stims
    """
    def __init__(self, stim_type, parameters, number):
        """
        Constructor
        :param stim_type: stim type_input pulled from parameter
        :param parameters: dictionary of parameters
        :param number: stim number order
        :return:
        """
        self.stim_type = stim_type
        self.parameters = parameters
        self.number = number

    def __str__(self):
        """
        for displaying info about the stim's passed parameters
        :return:
        """
        pp = pprint.PrettyPrinter(indent=2, width=1)
        return '\nStim #{}:\n{}:\n{}\n'.format(
            self.number, self.stim_type, str(pp.pformat(self.parameters)))


def input_parser(filename):
    """
    ****Not currently used.****
    parses input string passed by Igor GUI. Objects separated by
    pound sign. String format predetermined by Igor
    :param filename: name where input string is stored
    :return: returns list of StimInfo classes
    """
    # temp open file and read contents
    with open(filename, 'r') as f:
        s = f.read()

    # clean up string for parsing
    s = s.replace(' ', '')  # remove spaces
    s = s.replace("'", "")  # remove quotes
    s = s.replace(';', ',')  # replace semi-colons

    # remove comma from list items (i.e. location, color)
    p = re.compile('location= ([^,]*) , ([^[,#\]]*)', re.VERBOSE)
    s = p.sub(r'location=\1 \2', s)
    p = re.compile('color= ([^,]*), ([^,]*), ([^,]*)', re.VERBOSE)
    s = p.sub(r'color=\1 \2 \3', s)

    s = s.replace('=', ',')  # remove equals, make as csv
    s = s.lstrip('stim,[')  # remove starting extraneous
    s = s.rstrip(']')  # remove trailing

    list_of_dicts = []

    # store parameters in a list of dictionaries as param_name:param_value
    for i in range(s.count('#') + 1):
        # split off first set
        s = s.partition('#')
        s1, s = s[0], s[2]
        # turn into list
        l = s1.split(',')
        # create dict from list, taking every other value
        list_of_dicts.append(dict(zip(l[::2], l[1::2])))

    # cast number strings to ints or floats
    for item in list_of_dicts:
        for key, value in item.iteritems():
            try:
                item[key] = int(value)
            except ValueError:
                try:
                    item[key] = float(value)
                except ValueError:
                    pass

    # pull out "objectX: name" from dict and put value into temp_list
    temp_list = []
    for i in range(len(list_of_dicts)):
        temp_list.append(list_of_dicts[i].pop(next(
            k for k, v in list_of_dicts[i].items() if 'object' in k)))

    # create list of stims as list of StimInfo classes
    global list_of_stims  # to access for printing purposes
    # list of StimInfo classes
    list_of_stims = [StimInfo(temp_list[i], list_of_dicts[i], i + 1) for
                     i in range(len(temp_list))]

    return list_of_stims


class GlobalDefaults(object):
    """
    Class with global constants and window information
    """
    # use dictionary to simulate 'mutable static class variables'
    # better way to do this?
    defaults = {
    # defaults in case not run from GUI
        'frame_rate': 60,
        'pix_per_micron': 1,
        'scale': 1,
        'offset': [0, 0],
        'display_size': [400, 400],
        'position': [0, 0],
        'protocol_reps': 1,
        'background': [-1, 0, -1],
        'fullscreen': False,
        'log': False,
        'screen_num': 1,
        'trigger_wait': 0.1
    }

    def __init__(self, frame_rate=None, pix_per_micron=None, scale=None,
                 offset=None, display_size=None, position=None,
                 protocol_reps=None, background=None, fullscreen=None,
                 screen_num=None, trigger_wait=None, log=None):
        """
        Constructor
        """
        if frame_rate is not None:
            self.defaults['frame_rate'] = frame_rate
        if pix_per_micron is not None:
            self.defaults['pix_per_micron'] = pix_per_micron
        if scale is not None:
            self.defaults['scale'] = scale
        if offset is not None:
            self.defaults['offset'] = [offset[0] * pix_per_micron,
                                       offset[1] * pix_per_micron]
        if display_size is not None:
            self.defaults['display_size'] = display_size
        if position is not None:
            self.defaults['position'] = position
        if protocol_reps is not None:
            self.defaults['protocol_reps'] = protocol_reps
        if background is not None:
            self.defaults['background'] = background
        if fullscreen is not None:
            self.defaults['fullscreen'] = fullscreen
        if screen_num is not None:
            self.defaults['screen_num'] = screen_num
        if screen_num is not None:
            self.defaults['trigger_wait'] = trigger_wait
        if log is not None:
            self.defaults['log'] = log

    def __str__(self):
        """
        for displaying info about all stim parameters
        """
        pp = pprint.PrettyPrinter(indent=2, width=1)
        return '\n{} (all parameters):\n{}\n'.format(
            self.__class__.__name__, str(pp.pformat(vars(self))))

    def get_params(self):
        """
        function to return dictionary of all instance variables
        :return: dict of instance variables
        """
        return vars(self)


class StimDefaults(object):
    """
    Constructor class to hold parameter defaults
    """
    def __init__(self, shape="circle", fill_mode="uniform", orientation=0,
                 size_check_x=50, size_check_y=50, num_check=64, height=100,
                 width=50, outer_diameter=75, inner_diameter=40, delay=0,
                 duration=0.5, location=None, timing="step", intensity=1,
                 color=None, fill_seed=1, move_seed=1, speed=10,
                 num_dirs=4, start_dir=0, start_radius=300, travel_distance=50,
                 sf=1, contrast_channel="Green", movie_filename=None, movie_x_loc=0,
                 movie_y_loc=0, period_mod=1, image_width=100, image_height=100,
                 image_filename=None, table_filename=None, trigger=False):
        """
        default variable constructors, distance units converted appropriately
        """
        # parameter defaults
        self.shape = shape
        self.orientation = orientation
        self.fill_mode = fill_mode
        self.size_check_x = size_check_x * GlobalDefaults.defaults['pix_per_micron']
        self.size_check_y = size_check_y * GlobalDefaults.defaults['pix_per_micron']
        self.num_check = num_check
        self.height = height * GlobalDefaults.defaults['pix_per_micron']
        self.width = width * GlobalDefaults.defaults['pix_per_micron']
        self.outer_diameter = outer_diameter * GlobalDefaults.defaults['pix_per_micron']
        self.inner_diameter = inner_diameter * GlobalDefaults.defaults['pix_per_micron']
        self.delay = delay
        self.duration = duration
        self.timing = timing
        self.intensity = intensity
        self.fill_seed = fill_seed
        self.move_seed = move_seed
        self.speed = speed * GlobalDefaults.defaults['pix_per_micron'] / GlobalDefaults.defaults['frame_rate']
        self.num_dirs = num_dirs
        self.start_dir = start_dir
        self.start_radius = start_radius * GlobalDefaults.defaults['pix_per_micron']
        self.travel_distance = travel_distance * GlobalDefaults.defaults['pix_per_micron']
        self.sf = sf
        self.contrast_channel = contrast_channel
        self.movie_filename = movie_filename
        self.movie_x_loc = movie_x_loc * GlobalDefaults.defaults['pix_per_micron']
        self.movie_y_loc = movie_y_loc * GlobalDefaults.defaults['pix_per_micron']
        self.period_mod = period_mod
        self.image_filename = image_filename
        self.image_height = image_height
        self.image_width = image_width
        self.table_filename = table_filename
        self.trigger = trigger
        if location is None:
            self.location = [0, 0]
        else:
            self.location = [location[0] * GlobalDefaults.defaults[
                'pix_per_micron'],
                             location[1] * GlobalDefaults.defaults[
                'pix_per_micron']]
        if color is None:
            self.color = [-1, 1, -1]
        else:
            self.color = color


class Shape(StimDefaults):
    """
    Class for generic stim object
    """
    def __init__(self, **kwargs):
        """
        Constructor
        """
        # non parameter instance attributes
        self.start_stim = None
        self.end_stim = None
        self.draw_time = None
        self.stim = None
        self.grating_size = None
        self.desired_RGB = None

        # pass attributes up to super
        super(Shape, self).__init__(**kwargs)

        # seed randoms
        self.fill_random = Random()
        self.fill_random.seed(self.fill_seed)
        self.move_random = Random()
        self.move_random.seed(self.move_seed)

    # -----------------------------
    # methods for stimulus settings
    # -----------------------------

    def get_draw_times(self):
        """
        determines frames during which to draw stimulus
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults.defaults['frame_rate']
        self.end_stim = (self.duration * GlobalDefaults.defaults[
            'frame_rate']) + self.start_stim
        self.draw_time = self.end_stim - self.start_stim

        # return end stim time for calculating max frame time
        return self.end_stim

    def get_texture(self):
        """
        Determines texture, creates checkerboard array if necessary.
        ***RGB values in numpy textures are contrast values***
        :return: texture
        """
        # checkerboard texture
        if self.fill_mode == "checkerboard" or self.fill_mode == "random":
            # defaults entire board to color
            stim_texture = numpy.ones((self.num_check, self.num_check, 4),
                                      'f')
            # recolor checkerboard
            for i in xrange(self.num_check):
                for j in xrange(self.num_check):
                    # check board type_input
                    if self.fill_mode == 'random':
                        # if random is even
                        if (self.fill_random.randint(1, 2)) == 2:
                            # make black
                            stim_texture[i][j][1] = 0
                    elif self.fill_mode == 'checkerboard':
                        # even index of check
                        if (i + j) % 2 == 0:
                            # make transparent
                            stim_texture[i][j][3] = -1    # alpha

        # other textures
        elif self.fill_mode == "uniform":
            stim_texture = None

        elif self.fill_mode == "sine" or \
             self.fill_mode == "square" or \
             self.fill_mode == "concentric":
            # determine grating size (depends on shape)
            if self.shape == "rectangle":
                self.grating_size = self.width
            elif self.shape == "circle" or self.shape == "annulus":
                self.grating_size = self.outer_diameter

            stim_texture = numpy.ones((self.grating_size, self.grating_size,
                                       4), 'f')

            # change alpha values
            if self.fill_mode == "sine":
                stim_texture[:, :, 3] = (filters.makeGrating(self.grating_size,
                                                             gratType='sin',
                                                             cycles=1)) ** 2
            elif self.fill_mode == "square":
                stim_texture[:, :, 3] = (filters.makeGrating(self.grating_size,
                                                             gratType='sqr',
                                                             cycles=1) - 1) \
                                        / 2 + 1
            elif self.fill_mode == "concentric":
                stim_texture[:, :, 3] = (scipy.sin(filters.makeRadialMatrix(
                    self.grating_size)))

        return stim_texture

    def get_mask(self):
        """
        determines shape of stim
        :return: stim shape
        """
        if self.shape == "circle" or self.shape == "annulus":
            stim_mask = "circle"
        elif self.shape == "rectangle":
            stim_mask = None

        return stim_mask

    def get_size(self):
        """
        determines size of stim
        :return: size of stim as tuple
        """
        if self.fill_mode == 'image':
            stim_size = (self.image_width, self.image_height)
        elif self.shape == "circle" or self.shape == "annulus":
            stim_size = self.outer_diameter
        elif self.shape == "rectangle":
            if self.fill_mode == "random" or \
                            self.fill_mode == "checkerboard":
                stim_size = (self.num_check * self.size_check_x,
                             self.num_check * self.size_check_y)
            else:
                stim_size = (self.width, self.height)
        else:
            stim_size = (self.width, self.height)

        return stim_size

    def get_color_contrast(self):
        """
        determines color and contrast of stim
        :return: nothing
        """
        # see if color is passed as string
        try:
            stim_color = self.color.split(" ")
            # cast as ints
            for i in range(len(stim_color)):
                stim_color[i] = float(stim_color[i])
        # else already as list
        except (ValueError, AttributeError):
            stim_color = self.color

        # adjust contrast for specified channel, or globally
        if self.contrast_channel == "red":
            self.desired_RGB = [stim_color[0] * self.intensity,
                                stim_color[1],
                                stim_color[2]]
        if self.contrast_channel == "green":
            self.desired_RGB = [stim_color[0],
                                stim_color[1] * self.intensity,
                                stim_color[2]]
        if self.contrast_channel == "blue":
            self.desired_RGB = [stim_color[0],
                                stim_color[1],
                                stim_color[2] * self.intensity]
        if self.contrast_channel == "global":
            self.desired_RGB = [stim_color[0] * self.intensity,
                                stim_color[1] * self.intensity,
                                stim_color[2] * self.intensity]

        return self.desired_RGB

    def set_rgb(self, rgb):
        self.stim.setColor(rgb)

    def rgb_timing(self, frame):
        """
        determines contrast due to timing, recalculated on every call to
        animate()
        contrast multiplies RGB value
        :param frame: current frame number
        :return: nothing
        """
        current = frame - self.start_stim
        time_fraction = float(current) / self.draw_time

        # calculate color factor, which is the contrast as a function of time
        if self.timing == "sine":
            color_factor = (0.5 * scipy.sin(self.period_mod * scipy.pi *
                                            time_fraction - scipy.pi/2) + 0.5)
        elif self.timing == "square":
            color_factor = (scipy.signal.square(self.period_mod * 2 * scipy.pi *
                                          time_fraction, duty=0.5) - 1) / 2 + 1
        elif self.timing == "sawtooth":
            color_factor = (scipy.signal.sawtooth(self.period_mod * 2 * scipy.pi *
                                            time_fraction, width=1) - 1) / 2 + 1
        elif self.timing == "linear":
            color_factor = time_fraction

        elif self.timing == "step":
            color_factor = 1

        # multiply color by color factor
        if self.contrast_channel == "red":
            timing_rgb = [self.desired_RGB[0] * color_factor,
                          self.desired_RGB[1],
                          self.desired_RGB[2]]
        elif self.contrast_channel == "green":
            timing_rgb = [self.desired_RGB[0],
                          self.desired_RGB[1] * color_factor,
                          self.desired_RGB[2]]
        elif self.contrast_channel == "blue":
            timing_rgb = [self.desired_RGB[0],
                          self.desired_RGB[1],
                          self.desired_RGB[2] * color_factor]
        elif self.contrast_channel == "global":
            timing_rgb = [self.desired_RGB[0] * color_factor,
                          self.desired_RGB[1] * color_factor,
                          self.desired_RGB[2] * color_factor]

        return timing_rgb

    def get_timing(self, frame):
        return self.rgb_timing(frame)

    def get_phase(self):
        if self.grating_size is not None:
            self.stim.phase -= float(self.speed) / self.grating_size
        else:
            pass

    def make_stim(self):
        """
        instantiates PsychoPy stimulus object
        :return: nothing
        """
        if self.fill_mode == 'random' or self.fill_mode == 'checkerboard':
            self.__class__ = TestBoard
            self.make_stim()
        elif self.fill_mode == 'image':
            self.stim = visual.ImageStim(win=my_window,
                                     size=self.get_size(),
                                     pos=self.location,
                                     ori=self.orientation,
                                     image=self.image_filename,
                                     color=self.get_color_contrast())
        else:
            self.stim = visual.GratingStim(win=my_window,
                                           tex=self.get_texture(),
                                           mask=self.get_mask(),
                                           size=self.get_size(),
                                           pos=self.location,
                                           ori=self.orientation,
                                           color=self.get_color_contrast())
        # self.stim.sf *= self.sf
        # self.stim.phase = 1

    def animate(self, frame):
        """
        method for drawing objects to back buffer
        :param frame: current frame number
        :return: nothing
        """
        # if supposed to be drawn
        if self.start_stim <= frame < self.end_stim:
            # send trigger at just before first frame that stim object is drawn
            if self.trigger and self.start_stim == frame:
                send_trigger()
            self.set_rgb(self.get_timing(frame))
            # print "draw"
            self.stim.draw()
        else:
            pass


class MovingShape(Shape):
    """
    Class for moving shape stimuli, subclass of Shape
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param speed: pixels traveled per frame
        :param num_dirs: number of direction stim will travel
        :param start_dir:
        :param kwargs:
        :return:
        """
        # non parameter instance attributes
        self.current_x = None
        self.current_y = None
        self.frame_counter = None
        self.x_moves = None
        self.y_moves = None
        self.num_frames = None

        # pass parameters to super
        super(MovingShape, self).__init__(**kwargs)

    def get_draw_times(self):
        """
        determines frames during which to draw stimulus
        overrides super method
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults.defaults['frame_rate']

        # need to generate movement once to calculate num_frames
        self.generate_movement()
        self.end_stim = self.num_frames * self.num_dirs + self.start_stim
        self.draw_time = self.end_stim - self.start_stim

        # return end stim time for calculating max frame time
        return self.end_stim

    def get_move_array(self, start_x, start_y, angle, num_frames):
        """
        Calculates the new coordinates of the object for every frame
        Adapted from code by David L Morton, used under MIT License.
        Source: https://code.google.com/p/computational-neuroscience/
        source/browse/trunk/projects/electrophysiology/stimuli/
        randomly_moving_checkerboard_search.py
        :rtype : array tuple
        :param start_x: starting x coordinate
        :param start_y: starting y coordinate
        :param angle: travel direction
        :param num_frames: number of frames circle will travel for
        :return: the x,y coordinates of the circle in every frame as
        2 arrays
        """
        dx = self.speed * scipy.sin(angle * scipy.pi / 180.0)
        dy = self.speed * scipy.cos(angle * scipy.pi / 180.0)

        x = scipy.array([start_x + i * dx for i in xrange(num_frames)])
        y = scipy.array([start_y + i * dy for i in xrange(num_frames)])

        return x, y

    def get_starting_pos(self, direction):
        """
        Calculates starting position of the stim on start_radius in x,y
        coordinates based on travel direction
        :param direction: travel direction of stim object
        :return: starting position on border of frame based on travel
        angle origin
        """
        start_x = self.start_radius * scipy.sin(direction * scipy.pi / 180)
        start_y = self.start_radius * scipy.cos(direction * scipy.pi / 180)

        return start_x, start_y

    def generate_movement(self):
        """
        calls get_starting_pos() and get_move_array() with proper variables
        to get new movement coordinates
        :return: nothing
        """
        # current position trackers
        self.current_x, self.current_y = self.get_starting_pos(
            self.start_dir)

        # reset frame count
        self.frame_counter = 0

        # movement direction (travel dir is opposite of origin dir)
        if self.start_dir <= 180:
            angle = self.start_dir + 180
        else:
            angle = self.start_dir - 180

        # orient shape
        self.stim.ori = self.start_dir + 90

        # get movements and store for next_coordinate()
        # (+0.99 so int() rounds up)
        travel_distance = 2 * (
            (self.current_x ** 2 + self.current_y ** 2) ** 0.5)
        self.num_frames = int(travel_distance / self.speed + 0.99)
        self.x_moves, self.y_moves = self.get_move_array(self.current_x,
                                                         self.current_y,
                                                         angle,
                                                         self.num_frames)

        # set start_dir for next movement on next call
        self.start_dir += 360 / self.num_dirs

        # if passes 360 degrees, reset (for get_starting_pos())
        if self.start_dir >= 360:
            self.start_dir -= 360

    def get_next_coordinate(self):
        """
        returns the next coordinate for animate()
        :return:
        """
        x, y = self.x_moves[self.frame_counter], self.y_moves[
            self.frame_counter]
        # frame counter increment
        self.frame_counter += 1
        return x, y

    def set_position(self, x, y):
        self.stim.setPos((x, y))

    def animate(self, frame):
        """
        method for drawing objects to back buffer
        overrides super method
        :param frame: current frame number
        :return: nothing
        """
        # if within animation range
        if self.start_stim <= frame < self.end_stim:
            # sees if next coordinate exists/is calculated
            # else calls generate_movement() and retries
            try:
                x, y = self.get_next_coordinate()
                self.set_position(x, y)
                super(MovingShape, self).animate(frame)
                # self.get_phase()
            except (AttributeError, IndexError, TypeError):
                self.generate_movement()
                # send trigger on each new movement direction
                if self.trigger and self.__class__ == MovingShape:
                    send_trigger()
                self.animate(frame)
        else:
            pass


class TableStim(MovingShape):
    """
    class where object motion is determined by table of radial coordinates
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param kwargs:
        :return: nothing
        """
        # pass parameters to super
        super(TableStim, self).__init__(**kwargs)

    def get_draw_times(self):
        """
        determines frames during which to draw stimulus
        overrides super method
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults.defaults['frame_rate']

        # need to generate movement once to calculate num_frames
        frames = len(self.get_move_array()[0])
        self.end_stim = frames + self.start_stim
        self.draw_time = self.end_stim - self.start_stim

        # return end stim time for calculating max frame time
        return self.end_stim

    def get_move_array(self, *args):
        table = self.table_filename

        # if text file
        if os.path.splitext(table)[1] == '.txt':
            with open(table, 'r') as f:
                line = f.read()
                radius = line.split('\r')

        # if igor binary wave format
        elif os.path.splitext(table)[1] == '.ibw':
            radius = binarywave.load(table)['wave']['wData']

        # if igor packed experiment format
        elif os.path.splitext(table)[1] == '.pxp':
            radius = packed.load(table)[1]['root']['wave0'].wave['wave'][
                'wData']

        radius = map(float, radius)
        radius = [r * GlobalDefaults.defaults[
            'pix_per_micron'] for r in radius]

        # make coordinate array
        theta = self.start_dir * -1 + 90  # origins are different
        x, y = map(list, zip(*[pol2cart(theta, r) for r in radius]))

        return x, y

    def generate_movement(self):
        """
        Gets move array
        :return: nothing
        """
        self.frame_counter = 0
        self.x_moves, self.y_moves = self.get_move_array()


class RandomlyMovingShape(MovingShape):
    """
    Class for randomly moving shape stimuli
    """
    def __init__(self, **kwargs):
        """
        Constructor
        :param kwargs:
        :return: nothing
        """
        # pass parameters to super
        super(RandomlyMovingShape, self).__init__(**kwargs)

    def get_draw_times(self):
        """
        determines frames during which to draw stimulus, same as StimulusObject
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults.defaults['frame_rate']
        self.end_stim = (self.duration * GlobalDefaults.defaults[
            'frame_rate']) + self.start_stim
        self.draw_time = self.end_stim - self.start_stim

        # return end stim time for calculating max frame time
        return self.end_stim

    def get_position(self):
        return self.stim.pos

    def generate_movement(self):
        """
        calls get_starting_pos() and get_move_array() with proper variables
        to get new movement coordinates
        overrides super method
        :return: nothing
        """
        # current position trackers
        self.current_x, self.current_y = self.get_position()

        # reset frame count
        self.frame_counter = 0

        # random angle between 0 and 360
        angle = self.move_random.random() * 360

        # get movements array
        # +0.99 so int() rounds up
        num_frames = int(self.travel_distance / self.speed + 0.99)
        self.x_moves, self.y_moves = self.get_move_array(self.current_x,
                                                         self.current_y,
                                                         angle, num_frames)


# class NewBoard(visual.ElementArrayStim):
#     def __init__(self, **kwargs):
#
#         super(NewBoard, self).__init__(**kwargs)
#
#     def setPos(self, x, y):
#         self.setField((x, y))
#
#     def setColor(self, rgb):
#         pass


class TestBoard(RandomlyMovingShape):
    def __init__(self):
        # instance attributes
        self.colors = None

    def make_stim(self):
        xys = []
        for y in range(self.num_check/-2, self.num_check/2):
            for x in range(self.num_check/-2, self.num_check/2):
                xys.append((self.size_check_x*x, self.size_check_y*y))

        self.colors = numpy.ndarray((self.num_check**2, 3))
        self.colors[::] = GlobalDefaults.defaults['background']

        self.index = numpy.zeros((self.num_check, self.num_check))
        if self.fill_mode == 'checkerboard':
            self.index[0::2, 0::2] = 1
            self.index[1::2, 1::2] = 1
            self.index = numpy.concatenate(self.index[:])
        elif self.fill_mode == 'random':
            self.index = numpy.concatenate(self.index[:])
            for i in range(len(self.index)):
                self.index[i] = self.fill_random.randint(0,1)

        self.colors[numpy.where(self.index)] = self.get_color_contrast()

        self.stim = visual.ElementArrayStim(my_window,
                                            nElements=self.num_check**2,
                                            sizes=(self.size_check_x,
                                                   self.size_check_y),
                                            xys=xys, elementTex=None,
                                            colors=self.colors,
                                            elementMask=None)

    def set_position(self, x, y):
        self.stim.setFieldPos((x, y))

    def get_position(self):
        return self.stim.fieldPos

    def get_timing(self, frame):
        rgb = self.rgb_timing(frame)
        self.colors[numpy.where(self.index)] = rgb
        return self.colors

    def set_rgb(self, colors):
        # pass
        self.stim.setColors(colors)


class Movie(Shape):
    """
    Class for movie stimuli. Not currently functional.
    """
    def __init__(self, **kwargs):
        """
        constructor for movies
        :param filename:
        :param movie_x_loc:
        :param movie_y_loc:
        :param kwargs:
        :return:
        """

        # other instance attributes
        self.mov = None

        # super attribute instantiation
        super(Movie, self).__init__(**kwargs)

    def make_stim(self):
        """
        instantiates PsychoPy stimulus object
        :return: nothing
        """
        # load and start movie
        self.mov = visual.MovieStim(my_window, filename=self.movie_filename)
        self.mov.pause()

    def animate(self, frame):  # idk whats wrong not working
        # if within animation range
        if self.start_stim <= frame < self.end_stim:
            if self.start_stim == frame:
                self.mov.play()
            # play movie
            self.mov.draw()
            if self.end_stim == frame:
                self.mov.stop()


def send_trigger():
    """
    Triggers recording device by sending short voltage spike
    from a LabJack U3-HV
    :param wait: amount of time to pause after voltage spike
    :return: nothing
    """
    if has_u3:
        # initialize
        d = u3.U3()
        # voltage spike for 0.1 seconds with LED off flash
        # 0 low, 1 high, on flexible IO #4
        d.setFIOState(4, 1)
        # LED off
        d.getFeedback(u3.LED(State=False))
        core.wait(0.1)
        # reset
        d.setFIOState(4, 0)
        d.getFeedback(u3.LED(State=True))
        # wait x seconds
        core.wait(GlobalDefaults.defaults['trigger_wait'])
        d.close()
    elif not has_u3:
        print 'no labjack module/driver'


def run_stim(stim_list, verbose=False):
    """
    Function to run StimProgram. Generates stim objects and makes calls to
    animate.
    :param stim_list: list of StimInfo classes
    :param verbose: whether or not to print stim info
    :return:
    """
    reps = GlobalDefaults.defaults['protocol_reps']

    # print stim info
    if verbose:
        for i in range(len(stim_list)):
            print stim_list[i]


    # stat counters
    rep_count = 0
    frame_count = 0
    elapsed_time_count = 0

    # to exit out of nested loops
    global should_break
    should_break = False

    for x in range(reps):
        # prep stims
        to_animate = []
        for i in range(len(stim_list)):
            # if stim_list[i].parameters['fill_mode'] == 'checkerboard' or \
            #                 stim_list[i].parameters['fill_mode'] == 'random':
            #     to_animate.append(TestBoard(**stim_list[i].parameters))
            if not True:
                pass
            else:
                # instantiate stim objects by looking up string in globals()
                to_animate.append(globals()[stim_list[i].stim_type](
                    **stim_list[i].parameters))

                # if annulus, insert smaller white circle within larger circle
                if to_animate[i].shape == "annulus":
                    # make necessary changes to parameters
                    to_animate.append(globals()[stim_list[i].stim_type](
                        **stim_list[i].parameters))
                    to_animate[i + 1].outer_diameter = \
                        to_animate[i + 1].inner_diameter
                    to_animate[i + 1].timing = "step"
                    to_animate[i + 1].color = GlobalDefaults.defaults[
                        'background']
                    to_animate[i + 1].make_stim()

        # generate stims
        for i in range(len(to_animate)):
            to_animate[i].make_stim()

        # window time
        num_frames = int(max(to_animate[i].get_draw_times() for i in
                             range(len(to_animate))) + 0.99) - 1

        # timing clock
        elapsed = core.MonotonicClock()

        # draw and flip
        for n in xrange(num_frames):
            for i in range(len(to_animate)):
                to_animate[i].animate(n)
            my_window.flip()

            # escape key exit
            for key in event.getKeys():
                if key in ['escape']:
                    should_break = True
            if should_break:
                frame_count = n
                elapsed_time_count += elapsed.getTime()
                break
        if should_break:
            print "\nInterrupt!"
            break

        rep_count += 1
        elapsed_time_count += elapsed.getTime()

    # print some stats:
    """
    x rep(s) of x stim(s) generated.
    x/x frames displayed. Average fps: x hz.
    Elapsed time: x seconds.
    """
    print "\n{} rep(s) of {} stim(s) generated.". \
        format(reps, len(stim_list))
    print "{}/{} frames displayed.". \
        format(rep_count * num_frames + frame_count, reps * num_frames),
    print "Average fps: {0:.2f} hz.". \
        format((rep_count * num_frames + frame_count) / elapsed_time_count)
    print "Elapsed time: {0:.3f} seconds.\n". \
        format(elapsed_time_count)

    if GlobalDefaults.defaults['log']:
        time = localtime()
        time_string = strftime('%Y_%m_%d_%H%M%S', time)
        file_name = 'stimlog_' + time_string + '.txt'

        if sys.platform == 'darwin':
            path = config.get('StimProgram', 'logsDir')
            if not os.path.exists(path):
                os.makedirs(path)
            path += strftime('%Y_%m_%d', time) + '/'
            if not os.path.exists(path):
                os.makedirs(path)

        elif sys.platform == 'win32':
            path = config.get('StimProgram', 'logsDir')
            if not os.path.exists(path):
                os.makedirs(path)
            path += strftime('%Y_%m_%d', time) + '\\'
            if not os.path.exists(path):
                os.makedirs(path)

        with open((path+file_name), 'w') as f:
            f.write(strftime('%a, %d %b %Y %H:%M:%S', time))
            f.write("\n{} rep(s) of {} stim(s) generated. ". \
                format(reps, len(stim_list)))
            f.write("\n{}/{} frames displayed. ". \
                format(rep_count * num_frames + frame_count, reps * num_frames))
            f.write("Average fps: {0:.2f} hz.". \
                format((rep_count * num_frames + frame_count) / elapsed_time_count))
            f.write("\nElapsed time: {0:.3f} seconds.\n". \
                format(elapsed_time_count))
            for i in stim_list:
                f.write(str(i))
                f.write('\n')

            f.write('\n\n\n#BEGIN JSON#\n')
            to_write = []
            for i in stim_list:
                para_copy = copy.deepcopy(i.parameters)
                para_copy['move_type'] = i.stim_type
                to_write.append(para_copy)

            f.write(json.dumps(to_write))


def do_break():
    global should_break
    should_break = True


def main_wgui(params):
    run_stim(params)
    my_window.flip()


def make_window():
    global my_window
    mon = config.get('StimProgram', 'monitor')
    # print monitors.getAllMonitors()
    my_window = visual.Window(monitor=mon, units="pix",
                              size=GlobalDefaults.defaults['display_size'],
                              colorSpace="rgb", winType='pyglet',
                              allowGUI=False,
                              pos=GlobalDefaults.defaults['position'],
                              color=GlobalDefaults.defaults['background'],
                              fullscr=GlobalDefaults.defaults['fullscreen'],
                              viewPos=GlobalDefaults.defaults['offset'],
                              viewScale=GlobalDefaults.defaults['scale'],
                              screen=GlobalDefaults.defaults['screen_num']
                              )


def close_window():
    global my_window
    my_window.close()

if __name__ == "__main__":
    pass