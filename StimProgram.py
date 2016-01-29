#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Program for presenting visual stimuli to patch clamped retinal neurons.
"""

from psychopy import visual, logging, core, event, filters
from psychopy.tools.coordinatetools import pol2cart
from random import Random
from time import strftime, localtime
from PIL import Image
from math import copysign
from GammaCorrection import GammaValues  # necessary for pickling
import scipy
import scipy.signal
import numpy
import sys
import os
import cPickle
import copy
import ConfigParser
from tabulate import tabulate

try:
    from igor import binarywave, packed
    has_igor = True
except ImportError:
    has_igor = False

try:
    import u3
    has_u3 = True
except ImportError:
    has_u3 = False

__author__ =  "Alexander Tomlinson"
__license__ = "GPL"
__version__ = "1.1"
__email__ =   "tomlinsa@ohsu.edu"
__status__ =  "Beta"

# to suppress extra warnings, uncomment next line
# logging.console.setLevel(logging.CRITICAL)

# read ini file
config = ConfigParser.ConfigParser()
config.read('./psychopy/config.ini')


class StimInfo(object):
    """
    Class for storing type and parameters of a stim.

    :param string stim_type: The move type of the stim, such as static,
     random, table, etc.
    :param dict parameters: Dictionary of parameters passed from GUI.
    :param int number: For order of stims.
    """
    def __init__(self, stim_type, parameters, number):
        """
        Constructor.
        """
        self.stim_type = stim_type
        self.parameters = parameters
        self.number = number

    def __str__(self):
        """
        For printing information about the stim's parameters.
        :return: formatted string of parameter dictionary
        """
        to_print = '\nStim #{} ({}):\n'.format(self.number, self.stim_type)
        for k, v in sorted(self.parameters.items()):
            to_print += '   '
            to_print += str(k)
            to_print += ': '
            to_print += str(v)
            to_print += '\n'

        return to_print


class GlobalDefaultsMeta(type):
    """
    Metaclass to redefine get item for GlobalDefaults.
    """
    def __getitem__(self, item):
        return self.defaults[item]


class GlobalDefaults(object):
    """
    Class with global constants, such as window information. Uses dictionary
    to simulate 'mutable static class variables' (need better, more pythonic,
    way to do this).

    :param int frame_rate: Frame rate of monitor.
    :param float pix_per_micron: Number of pixels per micron. Used for unit
     conversion.
    :param float scale: The factor by which to scale the size of the stimuli.
    :param float display_size: List of height and width of the monitor.
    :param list position: List of xy coordinates of stim window location.
    :param int protocol_reps: Number of repetitions to cycle through of all
     stims.
    :param list background: RGB list of window background.
    :param bool fullscreen: Boolean, whether or not window should be fullscreen.
    :param int screen_num: On which monitor to display the window.
    :param string gamma_correction: Spline to use for gamma correction. See
     :doc:'GammaCorrection' documentation.
    :param float trigger_wait: The wait time between the labjack sending a
     pulse and the start of the stims.
    :param bool log: Whether or not to write to a log file.
    :param list offset: List of microns in xy coordinates of how much to
     offset the center of the window.
    """

    __metaclass__ = GlobalDefaultsMeta

    #: Dictionary of default defaults.
    defaults = dict(frame_rate=75,
                    pix_per_micron=1,
                    scale=1,
                    offset=[0, 0],
                    display_size=[400, 400],
                    position=[0, 0],
                    protocol_reps=1,
                    background=[-1, 0, -1],
                    fullscreen=False,
                    log=False,
                    screen_num=1,
                    gamma_correction='default',
                    trigger_wait=0.1)

    def __init__(self,
                 frame_rate=None,
                 pix_per_micron=None,
                 scale=None,
                 display_size=None,
                 position=None,
                 protocol_reps=None,
                 background=None,
                 fullscreen=None,
                 screen_num=None,
                 trigger_wait=None,
                 log=None,
                 gamma_correction=None,
                 offset=None):
        """
        Populate defaults if passed; units converted as necessary.
        """
        if frame_rate is not None:
            self.defaults['frame_rate'] = frame_rate

        if pix_per_micron is not None:
            self.defaults['pix_per_micron'] = pix_per_micron

        if scale is not None:
            self.defaults['scale'] = scale

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

        if gamma_correction is not None:
            self.defaults['gamma_correction'] = gamma_correction

        if offset is not None:
            self.defaults['offset'] = [offset[0],
                                       offset[1]]

    def __str__(self):
        """
        For pretty printing dictionary of global defaults
        """
        to_print = '\nGlobal Parameters: \n'
        for k, v in sorted(GlobalDefaults.defaults.items()):
            to_print += '   '
            to_print += str(k)
            to_print += ': '
            to_print += str(v)
            to_print += '\n'

        return to_print


class MyWindow(object):
    """
    Class with static methods for window management and triggering.
    """

    # Class attributes
    win = None
    gamma_mon = None
    should_break = False
    d = None

    @staticmethod
    def make_win():
        """
        Static method to create window from global parameters. Checks if
        gamma correction splines are present. Also instantiates labjack if
        present.
        """
        # create labjack instance
        if has_u3:
            MyWindow.d = u3.U3()

        # check if gamma splines present
        gamma = GlobalDefaults['gamma_correction']

        if gamma != 'default':
            gamma_file = './psychopy/gammaTables.txt'

            if os.path.exists(gamma_file):
                with open(gamma_file, 'rb') as f:
                    MyWindow.gamma_mon = cPickle.load(f)[gamma]

        # gamma correction as necessary
        if MyWindow.gamma_mon is not None:
            color = MyWindow.gamma_mon(GlobalDefaults['background'])
        else:
            color = GlobalDefaults['background']

        MyWindow.win = visual.Window(units='pix',
                                     colorSpace='rgb',
                                     winType='pyglet',
                                     allowGUI=False,
                                     color=color,
                                     size=GlobalDefaults['display_size'],
                                     pos=GlobalDefaults['position'],
                                     fullscr=GlobalDefaults['fullscreen'],
                                     viewPos=GlobalDefaults['offset'],
                                     viewScale=GlobalDefaults['scale'],
                                     screen=GlobalDefaults['screen_num'],
                                     monitor=config.get('StimProgram',
                                                        'monitor'))

    @staticmethod
    def close_win():
        """
        Static method to close window.
        """
        if has_u3:
            MyWindow.d.close()
        MyWindow.win.close()

    @staticmethod
    def send_trigger():
        """
        Triggers recording device by sending short voltage spike from LabJack
        U3-HV. Spike last approximately 0.4 ms. Ensure high enough sampling
        rate to reliably detect triggers.
        """
        # flip window to clear stims if wait time after trigger/between triggers
        if has_u3:
            if GlobalDefaults['trigger_wait'] != 0:
                MyWindow.win.flip()

            # voltage spike; 0 is low, 1 is high, on flexible IO #4
            MyWindow.d.setFIOState(4, 1)
            # reset
            MyWindow.d.setFIOState(4, 0)
            # wait
            core.wait(GlobalDefaults['trigger_wait'])


class StimDefaults(object):
    """
    Super class to hold parameter defaults. GUI passes dictionary of all
    parameters, whether used to make stim or not.
    """
    def __init__(self,
                 shape='circle',
                 fill_mode='uniform',
                 orientation=0,
                 size=None,
                 outer_diameter=75,
                 inner_diameter=40,
                 check_size=None,
                 num_check=64,
                 delay=0,
                 duration=0.5,
                 location=None,
                 timing='step',
                 intensity=1,
                 color=None,
                 color_mode='intensity',
                 fill_seed=1,
                 move_seed=1,
                 speed=10,
                 num_dirs=4,
                 start_dir=0,
                 start_radius=300,
                 travel_distance=50,
                 sf=1,
                 phase=None,
                 contrast_channel='Green',
                 movie_filename=None,
                 movie_size=None,
                 period_mod=1,
                 image_size=None,
                 image_filename=None,
                 table_filename=None,
                 trigger=False,
                 move_delay=0,
                 num_jumps=5,
                 jump_delay=100):
        """
        Default variable constructors; distance and time units converted
        appropriately.
        """
        self.shape = shape
        self.fill_mode = fill_mode
        self.orientation = orientation
        self.num_check = num_check
        self.timing = timing
        self.intensity = intensity
        self.fill_seed = fill_seed
        self.move_seed = move_seed
        self.num_dirs = num_dirs
        self.start_dir = start_dir
        self.sf = sf
        self.contrast_channel = contrast_channel
        self.movie_filename = movie_filename
        self.period_mod = period_mod
        self.image_filename = image_filename
        self.table_filename = table_filename
        self.trigger = trigger
        self.num_jumps = num_jumps
        self.color_mode = color_mode

        # list variables
        if color is not None:
            self.color = color
        else:
            self.color = [-1, 1, -1]

        if movie_size is not None:
            self.movie_size = movie_size
        else:
            self.movie_size = [100, 100]

        if phase is not None:
            self.phase = phase
        else:
            self.phase = [1, 1]

        # size conversions
        self.outer_diameter = outer_diameter * GlobalDefaults['pix_per_micron']
        self.inner_diameter = inner_diameter * GlobalDefaults['pix_per_micron']
        self.start_radius = start_radius * GlobalDefaults['pix_per_micron']
        self.travel_distance = travel_distance * GlobalDefaults['pix_per_micron']

        # time conversions
        self.delay = delay * GlobalDefaults['frame_rate']
        self.duration = duration * GlobalDefaults['frame_rate']
        self.move_delay = move_delay * GlobalDefaults['frame_rate']
        self.jump_delay = jump_delay * GlobalDefaults['frame_rate']

        # speed conversion
        self.speed = speed * (1.0 * GlobalDefaults['pix_per_micron'] /
                                    GlobalDefaults['frame_rate'])

        # list variable with unit conversion
        if location is not None:
            self.location = [location[0] * GlobalDefaults['pix_per_micron'],
                             location[1] * GlobalDefaults['pix_per_micron']]
        else:
            self.location = [0, 0]

        if size is not None:
            self.size = [size[0] * GlobalDefaults['pix_per_micron'],
                         size[1] * GlobalDefaults['pix_per_micron']]
        else:
            self.size = [100, 100]

        if movie_size is not None:
            self.movie_size = [movie_size[0] * GlobalDefaults['pix_per_micron'],
                               movie_size[1] * GlobalDefaults['pix_per_micron']]
        else:
            self.movie_size = [100, 100]

        if image_size is not None:
            self.image_size = [image_size[0] * GlobalDefaults['pix_per_micron'],
                               image_size[1] * GlobalDefaults['pix_per_micron']]
        else:
            self.movie_size = [100, 100]

        if check_size is not None:
            self.check_size = [check_size[0] * GlobalDefaults['pix_per_micron'],
                               check_size[1] * GlobalDefaults['pix_per_micron']]
        else:
            self.check_size = [100, 100]


class StaticStim(StimDefaults):
    """
    Class for generic non moving stims. Super class for other stim
    types. Stim object instantiated in make_stim(), and drawn with calls to
    animate().
    """
    def __init__(self, **kwargs):
        """
        Passes parameters up to super class. Seeds randoms.
        """
        # pass parameters up to super
        super(StaticStim, self).__init__(**kwargs)

        # non parameter instance attributes
        self.start_stim = None
        self.end_stim = None
        self.draw_duration = None
        self.stim = None
        self.grating_size = None
        self.contrast_adj_rgb = None

        # seed fill and move randoms
        self.fill_random = Random()
        self.fill_random.seed(self.fill_seed)
        self.move_random = Random()
        self.move_random.seed(self.move_seed)

    def make_stim(self):
        """
        Creates instance of psychopy stim object.
        """
        if self.fill_mode == 'image':
            self.stim = visual.ImageStim(win=MyWindow.win,
                                         size=self.gen_size(),
                                         color=self.gen_rgb(),
                                         pos=self.location,
                                         ori=self.orientation,
                                         image=self.image_filename)

        else:
            self.stim = visual.GratingStim(win=MyWindow.win,
                                           size=self.gen_size(),
                                           mask=self.gen_mask(),
                                           tex=self.gen_texture(),
                                           pos=self.location,
                                           # phase=self.gen_phase(),
                                           ori=self.orientation)

            self.stim.sf *= self.sf
            self.stim.phase = self.gen_phase()

    def draw_times(self):
        """
        Determines during which frames stim should be drawn, based on desired
        delay and duration times.

        :return: last frame number as int
        """
        self.start_stim = self.delay

        self.end_stim = self.duration
        self.end_stim += self.start_stim
        self.end_stim = int(self.end_stim + 0.99) - 1

        self.draw_duration = self.end_stim - self.start_stim

        return self.end_stim

    def animate(self, frame):
        """
        Method for drawing stim objects to back buffer. Checks if object
        should be drawn. Back buffer is brought to front with calls to flip()
        on the window. Sends trigger at beginning of animation.

        :param frame: current frame number
        """
        # check if within animation range
        if self.start_stim <= frame < self.end_stim:
            # adjust colors based on timing
            # if self.fill_mode != 'movie':
            #     self.set_rgb(self.gen_timing(frame))
            # draw to back buffer
            self.stim.draw()
            # trigger just before window flip
            if self.trigger and self.start_stim == frame:
                MyWindow.send_trigger()

    def gen_phase(self):
        """
        Determines the phase of the stim object. Converts from scalar values
        to xy values

        :return: the phase of the stim, as an xy list pair
        """
        if self.shape in ['circle', 'annulus']:
            stim_mask = 'circle'

        elif self.shape == 'rectangle':
            stim_mask = None

        return self.phase

    def gen_size(self):
        """
        Calculates sizes of various sims.

        :return: size of stim, as float for circles/annuli and height width
         tuple for other shapes
        """
        if self.fill_mode == 'image':
            stim_size = (self.image_size[0], self.image_size[1])

        elif self.shape in ['circle', 'annulus']:
            stim_size = (self.outer_diameter, self.outer_diameter)

        elif self.shape == 'rectangle':
            stim_size = (self.size[0], self.size[1])

        return stim_size

    def gen_mask(self):
        """
        Determines the mask of the stim object. The mask determines the shape of
        the stim. See psychopy documentation for more details.

        :return: mask of the stim object, as a string
        """
        if self.shape in ['circle', 'annulus']:
            stim_mask = 'circle'

        elif self.shape == 'rectangle':
            stim_mask = None

        return stim_mask

    def gen_texture(self):
        """
        Generates texture for stim object. If not none, textures are 3D numpy
        arrays. The first 3 values are contrast values applied to the rgb
        value, and the fourth is an alpha value (transparency mask). Textures
        are created by modulating the alpha value while contrast values are
        left as one (preserve rgb color selection).

        :return: texture, either None or a numpy array

        if self.fill_mode == 'uniform':
            stim_texture = None

        elif self.fill_mode in ['sine', 'square', 'concentric']:
            # grating size depends on shape
            if self.shape == 'rectangle':
                self.grating_size = self.size[0]

            elif self.shape in ['circle', 'annulus']:
                self.grating_size = self.outer_diameter

            # populate numpy array with ones as floats
            stim_texture = numpy.ones((self.grating_size, self.grating_size,
                                       4), 'f')

            # change alpha values. Alpha values are assigned by using
            # psychopy helper functions to create appropriate gratings
            if self.fill_mode == 'sine':
                stim_texture[:, :, 3] = (filters.makeGrating(
                        self.grating_size, gratType='sin', cycles=1)) ** 2

            elif self.fill_mode == 'square':
                stim_texture[:, :, 3] = (filters.makeGrating(
                        self.grating_size, gratType='sqr', cycles=1) - 1) / 2\
                                        + 1

            elif self.fill_mode == 'concentric':
                stim_texture[:, :, 3] = scipy.sin(filters.makeRadialMatrix(
                        self.grating_size))

        return stim_texture"""

        off = [-1, -1, -1]

        texture = numpy.zeros(self.gen_size()+(3,))
        texture[:, :,] = off

        intensity = self.intensity
        background = map(float,GlobalDefaults['background'])

        channel = ['red', 'green', 'blue', 'global'].index(self.contrast_channel)

        color = ((background[channel]+1)/2 + copysign((background[
                                                           channel]+1)/2 *
                                                      abs(intensity),
                                                      intensity)) * 2 - 1

        texture[:, :, channel] = color
        print color
        return texture

    def gen_rgb(self):
        """
        Adjusts initial rgb values for contrast in specified channel.
        :return: list of rgb values as floats
        """
        if self.contrast_channel == 'red':
            self.contrast_adj_rgb = [self.color[0] * self.intensity,
                                     self.color[1],
                                     self.color[2]]
        if self.contrast_channel == 'green':
            self.contrast_adj_rgb = [self.color[0],
                                     self.color[1] * self.intensity,
                                     self.color[2]]
        if self.contrast_channel == 'blue':
            self.contrast_adj_rgb = [self.color[0],
                                     self.color[1],
                                     self.color[2] * self.intensity]
        if self.contrast_channel == 'global':
            self.contrast_adj_rgb = [self.color[0] * self.intensity,
                                     self.color[1] * self.intensity,
                                     self.color[2] * self.intensity]

        return self.contrast_adj_rgb

    def gen_timing(self, frame):
        """
        Adjusts contrast values of stims based on desired timing (i.e. as a
        function of current frame / draw time). Recalculated on every call to
        animate(). Also adjusts for gamma correction if necessary.

        TODO: precompute values
        :param frame: current frame number
        :return: list of rgb values as floats
        """
        stim_frame_num = frame - self.start_stim
        time_fraction = stim_frame_num * 1.0 / self.draw_duration

        # calculate color factors, which are normalized to oscillate between 0
        # and 1 to avoid negative contrast values
        if self.timing == 'sine':
            color_factor = scipy.sin(self.period_mod * scipy.pi *
                                     time_fraction - scipy.pi / 2) / 2 + 0.5

        elif self.timing == 'square':
            color_factor = (scipy.signal.square(self.period_mod * 2 *
                                                scipy.pi * time_fraction,
                                                duty=0.5) + 1) / 2

        elif self.timing == 'sawtooth':
            color_factor = (scipy.signal.sawtooth(self.period_mod * 2 *
                                                  scipy.pi * time_fraction,
                                                  width=1) + 1) / 2

        elif self.timing == 'linear':
            color_factor = time_fraction

        elif self.timing == 'step':
            color_factor = 1

        # multiply rgbs by color factor, in proper contrast channel
        if self.contrast_channel == 'red':
            timing_adj_rgb = [self.contrast_adj_rgb[0] * color_factor,
                              self.contrast_adj_rgb[1],
                              self.contrast_adj_rgb[2]]
        if self.contrast_channel == 'green':
            timing_adj_rgb = [self.contrast_adj_rgb[0],
                              self.contrast_adj_rgb[1] * color_factor,
                              self.contrast_adj_rgb[2]]
        if self.contrast_channel == 'blue':
            timing_adj_rgb = [self.contrast_adj_rgb[0],
                              self.contrast_adj_rgb[1],
                              self.contrast_adj_rgb[2] * color_factor]
        if self.contrast_channel == 'global':
            timing_adj_rgb = [self.contrast_adj_rgb[0] * color_factor,
                              self.contrast_adj_rgb[1] * color_factor,
                              self.contrast_adj_rgb[2] * color_factor]

        if MyWindow.gamma_mon is not None:
            self.contrast_adj_rgb = MyWindow.gamma_mon(self.contrast_adj_rgb)

        return timing_adj_rgb

    def set_rgb(self, rgb):
        """
        Color setter.

        :param rgb: tuple or list of rgb values
        """
        self.stim.setColor(rgb)


class MovingStim(StaticStim):
    """
    Class for stims moving radially inwards. Overrides several classes.
    """
    def __init__(self, **kwargs):
        """
        Passes parameters up to super class.
        """
        # pass parameters up to super
        super(MovingStim, self).__init__(**kwargs)

        # non parameter instance attributes
        self.current_x = None
        self.current_y = None
        self.frame_counter = None
        self.x_array = None
        self.y_array = None
        self.num_frames = None
        self.trigger_frames = None

        # to track random motion positions
        self.log = [[], [0], []]  # angle, frame num, position

    def draw_times(self):
        """
        Determines during which frames stim should be drawn, based on desired
        delay and duration times. Overrides super method.

        :return: last frame number as int
        """
        self.start_stim = self.delay

        # need to generate movement to get number of frames
        self.gen_pos()

        self.end_stim = self.num_frames * self.num_dirs
        self.end_stim += self.start_stim

        self.draw_duration = self.end_stim - self.start_stim

        return self.end_stim

    def animate(self, frame):
        """
        Method for animating moving stims. Moves stims appropriately,
        then makes call to animate of super. Sends trigger on each
        recalculation of movements.

        :param frame: current frame number
        """
        # check if within animation range
        if self.start_stim <= frame < self.end_stim:
            # if next coordinate is calculated, moves stim, else calls
            # gen_movement() and retries
            try:
                x, y = self.get_next_pos()
                self.set_pos(x, y)

                if self.trigger_frames is not None and \
                        self.trigger_frames[frame]:
                    MyWindow.send_trigger()

                super(MovingStim, self).animate(frame)

            except (AttributeError, IndexError, TypeError):
                self.gen_pos()

                # log frame number for RandomlyMovingStim
                self.log[1].append(frame)

                if self.trigger:
                    MyWindow.send_trigger()

                # retry
                self.animate(frame)

    def gen_pos(self):
        """
        Makes calls to gen_start_pos() and gen_pos_array() with proper
        variables to get new array of position coordinates.
        """
        # update current position trackers
        self.current_x, self.current_y = self.gen_start_pos(self.start_dir)

        # reset frame counter
        self.frame_counter = 0

        # set movement direction (opposite of origin direction)
        angle = self.start_dir + 180
        if angle >= 360:
            angle -= 360

        # orient shape if not an image
        if self.fill_mode not in ['image', 'movie']:
            self.stim.ori = self.start_dir

        # calculate variables
        travel_distance = ((self.current_x**2 + self.current_y**2) ** 0.5) * 2
        self.num_frames = int(travel_distance / self.speed + 0.99)  # round up

        # generate position array
        self.x_array, self.y_array = self.gen_pos_array(self.current_x,
                                                        self.current_y,
                                                        self.num_frames,
                                                        angle)

        # add in move delay by placing stim off screen
        if len(self.stim.size) > 1:
            max_size = max(self.stim.size)
        else:
            max_size = self.stim.size

        off_x = (GlobalDefaults['display_size'][0] + max_size) / 2
        off_y = (GlobalDefaults['display_size'][1] + max_size) / 2

        for i in range(self.move_delay):
            self.x_array = scipy.append(self.x_array, off_x)
            self.y_array = scipy.append(self.y_array, off_y)

        self.num_frames += self.move_delay

        # set start_dir for next call of gen_pos()
        self.start_dir += 360 / self.num_dirs

        # start_dir cannot be more than 360
        if self.start_dir >= 360:
            self.start_dir -= 360

    def gen_start_pos(self, direction):
        """
        Calculates starting position in x, y coordinates on the starting
        radius based on travel direction.

        :param direction: starting position on border of frame based on travel
        :return: starting position on border of frame based on travel angle
         origin
        """
        start_x = self.start_radius * scipy.sin(direction * scipy.pi / 180)
        start_y = self.start_radius * scipy.cos(direction * scipy.pi / 180)

        return start_x, start_y

    def gen_pos_array(self, start_x, start_y, num_frames, angle):
        """
        Creates 2 arrays for x, y coordinates of stims for each frame.

        Adapted from code By David L. Morton, used under MIT License. Source:
        https://code.google.com/p/computational-neuroscience/source/browse/trunk/projects/electrophysiology/stimuli/randomly_moving_checkerboard_search.py/#40

        :param start_x: starting x coordinate
        :param start_y: starting y coordinate
        :param num_frames: number of frames stim will travel for
        :param angle: travel direction
        :return: the x, y coordinates of the stim for every frame as 2 arrays
        """
        dx = self.speed * scipy.sin(angle * scipy.pi / 180.0)
        dy = self.speed * scipy.cos(angle * scipy.pi / 180.0)

        x = scipy.array([start_x + i * dx for i in xrange(num_frames)])
        y = scipy.array([start_y + i * dy for i in xrange(num_frames)])

        return x, y

    def get_next_pos(self):
        """
        Returns the next coordinate from x, y_array for animate to set the
        position of the stim for the next frame.
        :return: x, y coordinate as tuple
        """
        x = self.x_array[self.frame_counter]
        y = self.y_array[self.frame_counter]

        # increment frame counter
        self.frame_counter += 1

        return x, y

    def set_pos(self, x, y):
        """
        Position setter. Necessary for alternate position setting in subclasses.

        :param x: x coordinate
        :param y: y coordinate
        """
        self.stim.setPos((x, y))

    def get_pos(self):
        """
        Position getter.
        """
        return self.stim.pos


class RandomlyMovingStim(MovingStim):
    """
    Class for stims moving randomly. Overrides several classes.
    """
    def __init__(self, **kwargs):
        """
        Passes parameters up to super class.
        """
        # pass parameters up to super
        super(RandomlyMovingStim, self).__init__(**kwargs)

    def draw_times(self):
        """
        Determines during which frames stim should be drawn, based on desired
        delay and duration times. Uses StaticStim's method.

        :return: last frame number as int
        """
        self.gen_pos()
        return super(MovingStim, self).draw_times()

    def gen_pos(self):
        """
        Makes calls to gen_start_pos() and gen_pos_array() with proper
        variables to get new array of position coordinates. Overrides super.
        """
        # update current position
        self.current_x, self.current_y = self.get_pos()

        # reset frame count
        self.frame_counter = 0

        # random angle between 0 and 360
        angle = self.move_random.randint(0, 360)

        # add to log
        self.log[0].append(angle)
        self.log[2].append(self.get_pos())

        # calculate variables, round up
        self.num_frames = int(self.travel_distance / self.speed + 0.99)

        # generate position array
        self.x_array, self.y_array = self.gen_pos_array(self.current_x,
                                                        self.current_y,
                                                        self.num_frames,
                                                        angle)


class TableStim(MovingStim):
    """
    Class where stim motion is determined by a table of radial coordinates.

    Table can be a text file with new line separated values, or an Igor file
    in binary wave or packed experiment format. First column is distance from
    center of window in micrometers, and second column either 0 or 1,
    for whether or not to trigger. Trigger will occur right before frame with
    indicated position is flipped. First coordinate will always trigger (if
    stim is set to trigger).

    For a binary wave file, values must be for coordinates, and triggering
    will only happen on first coordinate. For packed experiment files,
    leave wave names as 'wave0' and 'wave1', where 'wave0' is coordinates and
    'wave1' is whether or not to trigger.
    """
    def __init__(self, **kwargs):
        """
        Passes parameters up to super.
        """
        super(TableStim, self).__init__(**kwargs)

    def draw_times(self):
        """
        Determines during which frames stim should be drawn, based on desired
        delay and duration times. Overrides super method.

        :return: last frame number as int
        """
        self.start_stim = self.delay

        # need to generate movement to get number of frames
        self.gen_pos()

        self.end_stim = self.num_frames + self.start_stim

        self.draw_duration = self.end_stim - self.start_stim

        return self.end_stim

    def gen_pos(self):
        """
        Overrides super method. Calls gen_pos_array() and resets frame counter.
        """
        self.frame_counter = 0
        self.x_array, self.y_array = self.gen_pos_array()

    def gen_pos_array(self, *args):
        """
        Creates 2 arrays for x, y coordinates of stims for each frame.

        :return: the x, y coordinates of the stim for every frame as 2 arrays
        :raises ImportError: if attempts to load from an Igor file without
        having the igor module
        """
        table = self.table_filename
        radii = None

        # if text file
        if os.path.splitext(table)[1] == '.txt':
            with open(table, 'r') as f:
                lines = [line.strip() for line in f]

            radii = [i.split()[0] for i in lines]
            self.trigger_frames = [i.split()[1] for i in lines]
            self.trigger_frames[0] = 0

        # if igor binary wave format or packed experiment format
        elif os.path.splitext(table)[1] in ['.ibw', '.pxp']:
            if has_igor:
                if os.path.splitext(table)[1] == '.ibw':
                    radii = binarywave.load(table)['wave']['wData']

                elif os.path.splitext(table)[1] == '.pxp':
                    radii = packed.load(table)[1]['root']['wave0'].wave[
                        'wave']['wData']
                    self.trigger_frames = packed.load(table)[1]['root'][
                        'wave1'].wave['wave']['wData']

            elif not has_igor:
                raise ImportError('Need igor python module to load \'.ibw\' '
                                  'or \'.pxp\' formats. Install module with '
                                  '\'pip install igor\'.')

        # convert strings to floats
        if radii is not None:
            radii = map(float, radii)
        else:
            raise IOError('File not a supported format. See docs for '
                          'reference.')
        if self.trigger_frames is not None:
            self.trigger_frames = map(int, self.trigger_frames)

        self.num_frames = len(radii)

        # convert pix to micrometers
        radii = [r * GlobalDefaults['pix_per_micron'] for r in radii]

        # make arrays
        theta = self.start_dir * -1 + 90  # origins are different in pol/cart
        x, y = map(list, zip(*[pol2cart(theta, r) for r in radii]))

        return x, y


class ImageJumpStim(StaticStim):
    """
    Class to jump through random areas on a larger image.

    Currently broken.
    """
    def __init__(self, **kwargs):
        # pass parameters up to super
        super(ImageJumpStim, self).__init__(**kwargs)

    def make_stim(self):
        """
        Creates buffer with rendered images. Images are sampled to size of
        window.
        """
        image = Image.open(self.image_filename)
        cropped_list = []
        self.stim = []

        mon_x = GlobalDefaults.defaults['display_size'][0]
        mon_y = GlobalDefaults.defaults['display_size'][1]

        for i in range(self.num_jumps):
            x = self.move_random.randint(0, image.size[0] - mon_x)
            y = self.move_random.randint(0, image.size[1] - mon_y)

            cropped = image.crop((x, y, x + mon_x, y + mon_y))
            cropped_list.append(cropped)
            cropped.show()

            pic = visual.SimpleImageStim(win=MyWindow.win,
                                         image=cropped)
            pic.draw()

            for j in range(self.jump_delay):
                self.stim.append(visual.BufferImageStim(MyWindow.win))

            MyWindow.win.clearBuffer()

    def get_draw_times(self):
        """
        Determines frames during which to draw stimulus.
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults.defaults['frame_rate']

        self.end_stim = len(self.stim) + self.start_stim

        self.draw_duration = self.end_stim - self.start_stim

        # return end stim time for calculating max frame time
        return self.end_stim

    def animate(self, frame):
        """
        Method for drawing stim objects to back buffer. Checks if object
        should be drawn. Back buffer is brought to front with calls to flip()
        on the window.

        :param frame: current frame number
        """
        if self.start_stim <= frame < self.end_stim:
            # send trigger at just before first frame that stim object is drawn
            if self.trigger and self.start_stim == frame:
                MyWindow.send_trigger()
            i = frame - self.delay * GlobalDefaults.defaults['frame_rate']
            # draw to back buffer
            self.stim[i].draw()


def board_texture_class(bases, **kwargs):

    class BoardTexture(bases):
        """
        Class for checkerboard or random board textures. Rather than grating
        stims, stims are ElementArrayStims and thus need to override several
        methods related to stim creation and positioning, but otherwise
        implement parent methods.
        """
        def __init__(self):
            """
            Passes parameters up to super class.
            """
            # pass parameters up to super
            super(BoardTexture, self).__init__(**kwargs)

            # instance attributes
            self.index = None
            self.colors = None

        def make_stim(self):
            """
            Creates instance of psychopy stim object.
            """
            # array of coordinates for each element
            xys = []
            # populate xys
            for y in range(self.num_check/-2, self.num_check/2):
                for x in range(self.num_check/-2, self.num_check/2):
                    xys.append((self.check_size[0]*x, self.check_size[1]*y))

            # array of rgbs for each element
            self.colors = numpy.ndarray((self.num_check ** 2, 3))
            self.colors[::] = GlobalDefaults['background']

            # index to know how to color elements in array
            self.index = numpy.zeros((self.num_check, self.num_check))

            # populate every other for a checkerboard
            if self.fill_mode == 'checkerboard':
                self.index[0::2, 0::2] = 1
                self.index[1::2, 1::2] = 1
                self.index = numpy.concatenate(self.index[:])

            # randomly populate for a random checkerboard
            elif self.fill_mode == 'random':
                self.index = numpy.concatenate(self.index[:])
                for i in range(len(self.index)):
                    self.index[i] = self.fill_random.randint(0, 1)

            # use index to assign colors
            print self.colors
            print self.index
            self.colors[numpy.where(self.index)] = self.gen_rgb()

            self.stim = visual.ElementArrayStim(MyWindow.win,
                                                xys=xys,
                                                colors=self.colors,
                                                nElements=self.num_check**2,
                                                elementMask=None,
                                                elementTex=None,
                                                sizes=(self.check_size[0],
                                                       self.check_size[1]))

        def gen_timing(self, frame):
            """
            Calls super method to get adjusted rgbs then properly assigns
            values to stim array.

            :param frame: current frame number
            :return: array of adjusted rgbs
            """
            rgb = super(BoardTexture, self).gen_timing(frame)
            self.colors[numpy.where(self.index)] = rgb

            return self.colors

        def set_rgb(self, colors):
            """
            Colors setter.

            :param colors: array of rgb values for each element
            """
            self.stim.setColors(colors)

        def set_pos(self, x, y):
            """
            Position setter. Moves entire array of elements

            :param x: x coordinate
            :param y: y coordinate
            """
            self.stim.setFieldPos((x, y))

        def get_pos(self):
            """
            Position getter.
            """
            return self.stim.fieldPos

    return BoardTexture()


def movie_stim_class(bases, **kwargs):

    class MovieStim(bases):
        """
        Movie stims require a unique animate() method, but are otherwise
        similar to other stims.
        """
        def __init__(self):
            """
            Passes parameters up to super class.
            """
            # pass parameters up to super
            super(MovieStim, self).__init__(**kwargs)

        def make_stim(self):
            """
            Creates instance of psychopy stim object.
            """
            self.stim = visual.MovieStim(win=MyWindow.win,
                                         filename=self.movie_filename,
                                         pos=self.location,
                                         size=self.movie_size,
                                         loop=True)

        def animate(self, frame):
            """
            Method for drawing stim objects to back buffer. Checks if object
            should be drawn. Back buffer is brought to front with calls to
            flip() on the window. Sends trigger at beginning of animation.

            :param frame: current frame number
            """
            # check if within animation range
            if self.end_stim == (frame + 1):
                self.stim.pause()

            super(MovieStim, self).animate(frame)

    return MovieStim()


def log_stats(count_reps, reps, count_frames, num_frames, elapsed_time,
              stim_list, to_animate, time_at_run):
    """
    Function to write information about stims to file.

    :param count_reps: Elapsed reps.
    :param reps: Total possible reps.
    :param count_frames: Elapsed frames.
    :param num_frames: Total possible frames.
    :param elapsed_time: Elapsed time
    :param stim_list: List of stims that ran.
    :param time_at_run: Time at which stims were run
    """
    current_time = time_at_run
    current_time_string = strftime('%Y_%m_%d_%H%M%S', current_time)

    if sys.platform == 'win32':
        # log folder
        path = config.get('StimProgram', 'logsDir')
        if not os.path.exists(path):
            os.makedirs(path)
        # day folder
        path += strftime('%Y_%m_%d', current_time) + '\\'
        if not os.path.exists(path):
            os.makedirs(path)

    elif sys.platform == 'darwin':
        # log folder
        path = config.get('StimProgram', 'logsDir')
        if not os.path.exists(path):
            os.makedirs(path)
        # day folder
        path += strftime('%Y_%m_%d', current_time) + '/'
        if not os.path.exists(path):
            os.makedirs(path)

    # filename format: stimlog_[time]_[stimtype].txt
    file_name = 'stimlog_' + current_time_string + '_' + stim_list[
        0].stim_type.lower() + '.txt'

    with open((path+file_name), 'w') as f:
        f.write(strftime('%a, %d %b %Y %H:%M:%S', current_time))

        f.write("\n{} rep(s) of {} stim(s) generated. ".
                format(reps, len(stim_list)))

        f.write("\n{}/{} frames displayed. ".
                format(count_reps * num_frames + count_frames, reps *
                       num_frames))

        f.write("Average fps: {0:.2f} hz.".
                format((count_reps * num_frames + count_frames) / elapsed_time))

        f.write("\nElapsed time: {0:.3f} seconds.\n".format(elapsed_time))

        for i in stim_list:
            f.write(str(i))
            f.write('\n')

        f.write('\n\n\n#BEGIN PICKLE#\n')

    with open((path+file_name), 'ab') as f:
        # Pickle dump to be able to load parameters from log file of stim,
        # opened as binary, hence opening twice
        to_write = []
        for i in stim_list:
            para_copy = copy.deepcopy(i.parameters)
            para_copy['move_type'] = i.stim_type
            to_write.append(para_copy)

        f.write(cPickle.dumps(to_write))

    for i in range(len(stim_list)):
        if stim_list[i].stim_type == 'RandomlyMovingStim' and stim_list[
            i].parameters['shape'] != 'annulus':

            file_name = 'Randomlog_' + current_time_string + '_' + '.txt'
            with open((path+file_name), 'w') as f:

                temp = []
                for j in range(len(to_animate[i].log[0])):
                    temp.append([to_animate[i].log[0][j],
                                 to_animate[i].log[1][j],
                                 scipy.around(to_animate[i].log[2][j][0], 2),
                                 scipy.around(to_animate[i].log[2][j][1], 2)])

                f.write(tabulate(temp,
                                 headers=['angle', 'frame', 'pos x', 'pos y'],
                                 tablefmt="orgtbl"))

                f.write('\n\nangle list:\n')

                for j in range(len(to_animate[i].log[0])):
                    f.write(str(to_animate[i].log[0][j]))
                    f.write('\n')

                f.write('\nframe list:\n')

                for j in range(len(to_animate[i].log[0])):
                    f.write(str(to_animate[i].log[1][j]))
                    f.write('\n')

                f.write('\nx position list:\n')

                for j in range(len(to_animate[i].log[0])):
                    f.write(str(to_animate[i].log[2][j][0]))
                    f.write('\n')

                f.write('\ny position list:\n')

                for j in range(len(to_animate[i].log[0])):
                    f.write(str(to_animate[i].log[2][j][1]))
                    f.write('\n')


def main(stim_list, verbose=True):
    """
    Function to animate stims. Creates instances of stim types, and makes
    necessary calls to animate stims and flip window.

    :param stim_list: List of StimInfo classes.
    :param verbose: Whether or not to print stim info to console.
    """
    current_time = localtime()

    reps = GlobalDefaults['protocol_reps']

    # print stim info if requested
    #if verbose:
    #    for stim in stim_list:
    #        print stim

    # counters for stat tracking
    count_reps = 0
    count_frames = 0
    count_elapsed_time = 0

    # to exit out of nested loops
    MyWindow.should_break = False

    # outer loop for number of reps
    for x in range(reps):
        # prep stims
        to_animate = []

        for stim in stim_list:
            # checkerboard and movie inheritance depends on motion type,
            # so instantiate accordingly
            if stim.parameters['fill_mode'] in ['checkerboard', 'random']:
                to_animate.append(board_texture_class(globals()[
                                                          stim.stim_type],
                                  **stim.parameters))
            elif stim.parameters['fill_mode'] == 'movie':
                to_animate.append(movie_stim_class(globals()[stim.stim_type],
                                  **stim.parameters))

            # all other stims, instantiate by looking up class in globals(), and
            # pass dictionary of parameters
            else:
                to_animate.append(globals()[stim.stim_type](**stim.parameters))

            # annuli are handled by creating a duplicate smaller nested
            # circle within the larger circle, and setting its color to
            # background and its timing to instant
            if stim.parameters['shape'] == 'annulus':
                # make necessary changes
                stim.parameters['timing'] = 'step'
                stim.parameters['color'] = GlobalDefaults['background']
                stim.parameters['outer_diameter'] = stim.parameters[
                    'inner_diameter']

                # add
                to_animate.append(globals()[stim.stim_type](**stim.parameters))

        # generate stims
        for stim in to_animate:
            stim.make_stim()

        # determine end time of last stim
        num_frames = max(stim.draw_times() for stim in to_animate)
        # round up, then subtract 1 because index starts at 0
        # num_frames = int(num_frames + 0.99) - 1

        # clock for timing
        elapsed_time = core.MonotonicClock()

        # draw stims and flip window
        for frame in xrange(num_frames):
            for stim in to_animate:
                stim.animate(frame)
            MyWindow.win.flip()

            # escape key breaks if focus on window
            for key in event.getKeys(keyList=['escape']):
                if key in ['escape']:
                    MyWindow.should_break = True

            # inner break
            if MyWindow.should_break:
                count_frames = frame + 1
                # count_elapsed_time += elapsed_time.getTime()
                break

        # get elapsed time for fps
        count_elapsed_time += elapsed_time.getTime()

        # stop movies from continuing in background
        for stim in to_animate:
            if stim.fill_mode == 'movie':
                stim.stim.pause()

        # outer break
        if MyWindow.should_break:
            print '\n Interrupt!'
            break

        count_reps += 1

    # one last flip to clear window
    MyWindow.win.flip()

    # print some stats
    if verbose:
        """
        x rep(s) of x stim(s) generated.
        x/x frames displayed. Average fps: x hz.
        Elapsed time: x seconds.
        """
        print "\n{} rep(s) of {} stim(s) generated.". \
            format(reps, len(stim_list))
        print "{}/{} frames displayed.". \
            format(count_reps * (num_frames+1) + count_frames, reps *
                   (num_frames+1)),
        print "Average fps: {0:.2f} hz.". \
            format((count_reps * (num_frames+1) + count_frames) / count_elapsed_time)
        print "Elapsed time: {0:.3f} seconds.\n". \
            format(count_elapsed_time)


    if GlobalDefaults['log']:
        log_stats(count_reps, reps, count_frames, num_frames,
                  count_elapsed_time, stim_list, to_animate, current_time)

if __name__ == '__main__':
    pass
