#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Program for presenting visual stimuli to patch clamped retinal neurons"
"""

from psychopy import visual, logging, core, event, filters, monitors
from psychopy.tools.coordinatetools import pol2cart
from random import Random
from time import strftime, localtime
from igor import binarywave, packed
from pprint import PrettyPrinter
import scipy
import numpy
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

__author__ =  "Alexander Tomlinson"
__license__ = "GPL"
__version__ = "1.0"
__email__ =   "tomlinsa@ohsu.edu"
__status__ =  "Beta"

# to suppress extra warnings, uncomment next line
# logging.console.setLevel(logging.CRITICAL)

# read ini file
config = ConfigParser.ConfigParser()
config.read('.\psychopy\config.ini')

class StimInfo(object):
    """
    class for storing type and parameters of a stim
    """
    def __init__(self, stim_type, parameters, number):
        """
        constructor
        :param stim_type: the move type of the stim, such as static, random,
        table, etc.
        :param parameters: dictionary of parameters passed from GUI
        :param number: for order of stims
        """
        self.stim_type = stim_type
        self.parameters = parameters
        self.number = number

    def __str__(self):
        """
        for printing information about the stim's parameters
        :return: formatted string of parameter dictionary
        """
        return '\nStim #{}:\n{}:\n{}\n'.format(
            self.number, self.stim_type, str(PrettyPrinter(indent=2,
                width=1).pformat(self.parameters)))


class GlobalDefaults(object):
    """
    Class with global constants, such as window information. Uses dictionary
    to simulate 'mutable static class variables' (need better, more pythonic, way to do this)
    """

    # default defaults
    defaults = dict(frame_rate=60,
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
                 offset=None):
        """
        Populate defaults; units converted as necessary
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

        if offset is not None:
            self.defaults['offset'] = [offset[0] * pix_per_micron,
                                       offset[1] * pix_per_micron]

    def __str__(self):
        """
        for pretty printing dictionary of global defaults
        """
        return '\n{} (all parameters):\n{}\n'.format(
            self.__class__.__name__, str(PrettyPrinter(indent=2,
                width=1).pformat(vars(self))))


class StimDefaults(object):
    """
    Super class to hold parameter defaults
    """
    def __init__(self,
                 shape="circle",
                 fill_mode="uniform",
                 orientation=0,
                 height=100,
                 width=50,
                 outer_diameter=75,
                 inner_diameter=40,
                 size_check_x=50,
                 size_check_y=50,
                 num_check=64,
                 delay=0,
                 duration=0.5,
                 location=None,
                 timing="step",
                 intensity=1,
                 color=None,
                 fill_seed=1,
                 move_seed=1,
                 speed=10,
                 num_dirs=4,
                 start_dir=0,
                 start_radius=300,
                 travel_distance=50,
                 sf=1,
                 contrast_channel="Green",
                 movie_filename=None,
                 movie_x_loc=0,
                 movie_y_loc=0,
                 period_mod=1,
                 image_width=100,
                 image_height=100,
                 image_filename=None,
                 table_filename=None,
                 trigger=False):
        """
        default variable constructors; distance units converted appropriately
        """
        self.shape = shape
        self.fill_mode = fill_mode
        self.orientation = orientation
        self.num_check = num_check
        self.delay = delay
        self.duration = duration
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
        self.image_width = image_width
        self.image_height = image_height
        self.image_filename = image_filename
        self.table_filename = table_filename
        self.trigger = trigger

        # list variable
        if color is None:
            self.color = [-1, 1, -1]
        else:
            self.color = color

        # unit conversions
        self.size_check_x = size_check_x * GlobalDefaults.defaults[
            'pix_per_micron']
        self.size_check_y = size_check_y * GlobalDefaults.defaults[
            'pix_per_micron']
        self.height = height * GlobalDefaults.defaults[
            'pix_per_micron']
        self.width = width * GlobalDefaults.defaults[
            'pix_per_micron']
        self.outer_diameter = outer_diameter * GlobalDefaults.defaults[
            'pix_per_micron']
        self.inner_diameter = inner_diameter * GlobalDefaults.defaults[
            'pix_per_micron']
        self.start_radius = start_radius * GlobalDefaults.defaults[
            'pix_per_micron']
        self.travel_distance = travel_distance * GlobalDefaults.defaults[
            'pix_per_micron']
        self.movie_x_loc = movie_x_loc * GlobalDefaults.defaults[
            'pix_per_micron']
        self.movie_y_loc = movie_y_loc * GlobalDefaults.defaults[
            'pix_per_micron']

        # list variable with unit conversion
        if location is None:
            self.location = [0, 0]
        else:
            self.location = [location[0] * GlobalDefaults.defaults[
                'pix_per_micron'],
                             location[1] * GlobalDefaults.defaults[
                'pix_per_micron']]

        self.speed = speed * GlobalDefaults.defaults['pix_per_micron'] / \
                     GlobalDefaults.defaults['frame_rate']


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
        self.adjusted_rgb = None

        # seed fill and move randoms
        self.fill_random = Random()
        self.fill_random.seed(self.fill_seed)
        self.move_random = Random()
        self.move_random.seed(self.move_seed)

    def make_stim(self):
        """
        Creates instance of psychopy stim object
        """
        if self.fill_mode == 'image':
            self.stim = visual.ImageStim(win=my_window,
                                         size=self.gen_size(),
                                         color=self.gen_rgb(),
                                         pos=self.location,
                                         ori=self.orientation,
                                         image=self.image_filename
                                         )
        else:
            self.stim = visual.GratingStim(win=my_window,
                                           size=self.gen_size(),
                                           color=self.gen_rgb(),
                                           mask=self.gen_mask(),
                                           tex=self.gen_texture(),
                                           pos=self.location,
                                           ori=self.orientation
                                           )

    def draw_times(self):
        """
        Determines during which frames stim should be drawn, based on desired
        delay and duration times
        :return: last frame number as int
        """
        self.start_stim = self.delay * GlobalDefaults['frame_rate']

        self.end_stim = self.duration * GlobalDefaults['frame_rate']
        self.end_stim += self.start_stim

        self.draw_duration = self.end_stim - self.start_stim

        return self.end_stim

    def animate(self, frame):
        # draw times
        # set rgb
        pass

    def gen_size(self):
        """
        calculates sizes for various sims
        :return: size of stim, as float for circles/annuli and height width
        tuple for other shapes
        """
        if self.fill_mode == 'image':
            stim_size = (self.image_width, self.image_height)

        elif self.shape == 'circle' or self.shape == 'annulus':
            stim_size = self.outer_diameter

        elif self.shape == 'rectangle':
            if self.fill_mode == ('random' or 'checkerboard'):
                stim_size = (self.size_check_x * self.num_check,
                             self.size_check_y * self.num_check)

            else:
                stim_size = (self.width, self.height)

        else:
            stim_size = (self.width, self.height)

        return stim_size

    def gen_mask(self):
        """
        Determines the mask of the stim object. The mask determines the shape of
        the stim. See psychopy documentation for more details.
        :return: mask of the stim object, as a string
        """
        if self.shape == ('circle' or 'annulus'):
            stim_mask = 'circle'

        elif self.shape == 'rectangle':
            stim_mask = 'rectangle'

        return stim_mask

    def gen_texture(self):
        """
        Generates texture for stim object. If not none, textures are 3D numpy
        arrays, where the 3rd element is 4 values. The first 3 values are
        contrast values applied to the rgb value, and the fourth is an alpha
        value (transparency mask). Textures are created by modulating the alpha
        value while contrast values are left as one (preserve rgb color
        selection).

        :return: texture, either None or a numpy array
        """
        if self.fill_mode == 'uniform':
            stim_texture = None

        elif self.fill_mode == ('checkerboard' or 'random'):
            pass

        elif self.fill_mode == ('sine' or 'square' or 'concentric'):
            # grating size depends on shape
            if self.shape == 'rectangle':
                self.grating_size = self.width
            elif self.shape == ('circle' or 'annulus'):
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

    def gen_rgb(self):
        """
        Adjusts initial rgb values for contrast in specified channel.
        :return: list of rgb values as floats
        """
        if self.contrast_channel == 'red':
            self.adjusted_rgb = [self.color[0] * self.intensity,
                                 self.color[1],
                                 self.color[2]]
        if self.contrast_channel == 'green':
            self.adjusted_rgb = [self.color[0],
                                 self.color[1] * self.intensity,
                                 self.color[2]]
        if self.contrast_channel == 'blue':
            self.adjusted_rgb = [self.color[0],
                                 self.color[1],
                                 self.color[2] * self.intensity]
        if self.contrast_channel == 'global':
            self.adjusted_rgb = [self.color[0] * self.intensity,
                                 self.color[1] * self.intensity,
                                 self.color[2] * self.intensity]

        return self.adjusted_rgb

    def gen_timing(self, frame):
        """
        Adjusts contrast values of stims based on desired timing (i.e. as a
        function of current frame / draw time). Recalculated on every call to
        animate().
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
                                     time_fraction - scipy.pi/2) / 2 + 0.5

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

    def set_rgb(self, rgb):
        self.stim.setColor(rgb)