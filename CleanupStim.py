#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Program for presenting visual stimuli to patch clamped retinal neurons"
"""

from psychopy import visual, logging, core, event, filters
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

# suppress extra warnings
# logging.console.setLevel(logging.CRITICAL)

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
    class with global constants, such as window information
    """
    # use dictionary to simulate 'mutable static class variables'
    # need better, more pythonic, way to do this

    # default defaults
    defaults = {
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
        Constructor
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
        for displaying info about all stim parameters
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

        # unit conversion
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
    class for generic non moving stim object
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
        self.draw_time = None
        self.stim = None
        self.grating_size = None
        self.desired_RGB = None

        # seed randoms
        self.fill_random = Random()
        self.fill_random.seed(self.fill_seed)

        self.move_random = Random()
        self.move_random.seed(self.move_seed)

    def make_stim(self):
        # gen rgb
        # gen size
        # gen mask
        # gen texture
        # set location
        # set orientation
        pass

    def draw_times(self):
        pass

    def animate(self):
        # draw times
        # set rgb
        pass

    def gen_rgb(self):
        # rgb with contrast correction
        # gen timing
        pass

    def gen_timing(self):
        pass

    def gen_size(self):
        pass

    def gen_mask(self):
        pass

    def gen_texture(self):
        pass

    def set_rgb(self):
        # gen rgb
        pass

    def set_pos(self):
        pass

    def set_ori(self):
        pass