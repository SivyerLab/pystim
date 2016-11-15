"""
Program for presenting visual stimuli to patch clamped retinal neurons.

Stuck on python 2.7 because of u3 (labjackpython) dependency
"""

# Copyright (C) 2016 Alexander Tomlinson
# Distributed under the terms of the GNU General Public License (GPL).

from GammaCorrection import GammaValues  # unused, but necessary for pickling
from psychopy.tools.typetools import uint8_float, float_uint8
from psychopy.tools.coordinatetools import pol2cart
from psychopy import visual, core, event, filters
from time import strftime, localtime
from tqdm import tqdm, trange
from random import Random
from PIL import Image
from math import ceil

import scipy, scipy.signal
import sortedcontainers
import ConfigParser
import subprocess
import traceback
import cPickle
import numpy
import array
import copy
import sys
import os

global has_igor
try:
    from igor import binarywave, packed
    has_igor = True
except ImportError:
    has_igor = False

global has_tabulate
try:
    from tabulate import tabulate
    has_tabulate = True
except ImportError:
    has_tabulate = False

global has_u3
try:
    import u3
    has_u3 = True
except ImportError:
    has_u3 = False

__author__  = "Alexander Tomlinson"
__license__ = "GPL"
__version__ = "1.1"
__email__   = "tomlinsa@ohsu.edu"
__status__  = "Beta"

# to suppress extra warnings, uncomment next 2 lines
# from psychopy import logging
# logging.console.setLevel(logging.CRITICAL)

# read ini file
config = ConfigParser.ConfigParser()
config.read(os.path.abspath('../stimprogram/psychopy/config.ini'))


class StimInfo(object):
    """Class for storing type and parameters of a stim.

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

    def __repr__(self):
        """For printing information about the stim's parameters.

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
    """Metaclass to redefine get and set item for :py:class:`GlobalDefaults`.
    """
    def __getitem__(self, key):
        return self.defaults[key]

    def __setitem__(self, key, item):
        self.defaults[key] = item


class GlobalDefaults(object):
    """Class with global constants, such as window information.

    TODO: better, more pythonic, way to do this

    :param int frame_rate: Frame rate of monitor.
    :param float pix_per_micron: Number of pixels per micron. Used for unit
     conversion.
    :param float scale: The factor by which to scale the size of the stimuli.
    :param float display_size: List of height and width of the monitor.
    :param list position: List of xy coordinates of stim window location.
    :param int protocol_reps: Number of repetitions to cycle through of all
     stims.
    :param list background: RGB list of window background.
    :param float pref_dir: Cell preferred direction. If not -1, overrides
     start_dir.
    :param bool fullscreen: Boolean, whether or not window should be
     fullscreen.
    :param int screen_num: On which monitor to display the window.
    :param string gamma_correction: Spline to use for gamma correction. See
     :doc:'GammaCorrection' documentation.
    :param float trigger_wait: The wait time between the labjack sending a
     pulse and the start of the stims.
    :param bool log: Whether or not to write to a log file.
    :param list offset: List of microns in xy coordinates of how much to
     offset the center of the window.
    """

    # allow static __getitem__ and __setitem__
    __metaclass__ = GlobalDefaultsMeta

    #: Dictionary of default defaults.
    defaults = dict(frame_rate=60,
                    pix_per_micron=1,
                    scale=1,
                    offset=[0, 0],
                    display_size=[400, 400],
                    position=[0, 0],
                    protocol_reps=1,
                    background=[-1, 0, -1],
                    pref_dir=-1,
                    fullscreen=False,
                    log=False,
                    screen_num=1,
                    gamma_correction='default',
                    trigger_wait=6,
                    capture=False,
                    small_win=False)

    def __init__(self,
                 frame_rate=None,
                 pix_per_micron=None,
                 scale=None,
                 display_size=None,
                 position=None,
                 protocol_reps=None,
                 background=None,
                 pref_dir=None,
                 fullscreen=None,
                 screen_num=None,
                 trigger_wait=None,
                 log=None,
                 gamma_correction=None,
                 offset=None,
                 capture=None,
                 small_win=None):
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

        if pref_dir is not None:
            self.defaults['pref_dir'] = pref_dir

        if fullscreen is not None:
            self.defaults['fullscreen'] = fullscreen

        if screen_num is not None:
            self.defaults['screen_num'] = screen_num

        if trigger_wait is not None:
            self.defaults['trigger_wait'] = int(trigger_wait * 1.0 *
                                                frame_rate + 0.99)

        if log is not None:
            self.defaults['log'] = log

        if gamma_correction is not None:
            self.defaults['gamma_correction'] = gamma_correction

        if offset is not None:
            self.defaults['offset'] = [offset[0],
                                       offset[1]]

        if capture is not None:
            self.defaults['capture'] = capture

        if small_win is not None:
            self.defaults['small_win'] = small_win

    def __repr__(self):
        """For pretty printing dictionary of global defaults.
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
    """Class with static methods for window management and triggering.
    """
    # Class attributes
    #: Psychopy window instances.
    win = None
    small_win = None
    #: Gamma correction instance. See :py:class:`GammaCorrection`.
    gamma_mon = None
    #: Used to break out of animation loop in :py:func:`main`.
    should_break = False
    #: Labjack U3 instance for triggering.
    d = None
    #: List of frames to trigger on
    frame_trigger_list = sortedcontainers.SortedList()
    frame_trigger_list.add(sys.maxint)  # need an extra last value for indexing

    @staticmethod
    def make_win():
        """Static method to create window from global parameters. Checks if
        gamma correction splines are present. Also instantiates labjack if
        present.
        """

        # create labjack instance
        global has_u3
        if has_u3:
            try:
                MyWindow.d = u3.U3()
            except Exception as e:
                print 'LabJack error:',
                print e,
                print "(ignore if don't desire triggering)"
                has_u3 = False

        # check if gamma splines present
        gamma = GlobalDefaults['gamma_correction']

        if gamma != 'default':
            gamma_file = os.path.abspath('./psychopy/data/gammaTables.txt')

            if os.path.exists(gamma_file):
                with open(gamma_file, 'rb') as f:
                    MyWindow.gamma_mon = cPickle.load(f)[gamma]

        else:
            MyWindow.gamma_mon = None

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
                                     )

        MyWindow.win.mouseVisible = True,
        if GlobalDefaults['small_win']:
            MyWindow.make_small_win()

    @staticmethod
    def close_win():
        """Static method to close window. Also closes labjack if present.
        """
        if has_u3 and MyWindow.d is not None:
            MyWindow.d.close()
            MyWindow.d = None

        MyWindow.win.close()
        MyWindow.win = None

        if MyWindow.small_win is not None:
            MyWindow.small_win.close()
            MyWindow.small_win = None

    @staticmethod
    def change_color(color):
        """Static method to live update the background of the window.
        TODO: implement classproperty to make setter

        :param color: RGB list used to change global defaults.
        """
        try:
            if MyWindow.win is not None:
                GlobalDefaults['background'] = color

                if MyWindow.gamma_mon is not None:
                    color = MyWindow.gamma_mon(color)

                MyWindow.win.color = color

                if MyWindow.small_win is not None:
                    MyWindow.small_win.color = color

                # need to flip twice because of how color is updated on back
                # buffer
                MyWindow.flip()
                MyWindow.flip()

        except (ValueError, AttributeError):
            pass

    @staticmethod
    def make_small_win():
        """
        Makes a small window to see what's being show on the projector.
        """
        if GlobalDefaults['display_size'][0] > GlobalDefaults[
                'display_size'][1]:
            scaled_size = [400.0,
                           400.0 / GlobalDefaults['display_size'][0] *
                           GlobalDefaults['display_size'][1]]
        else:
            scaled_size = [400.0 / GlobalDefaults['display_size'][1] *
                           GlobalDefaults['display_size'][0],
                           400.0]

        scaled_scale = [scaled_size[0] / GlobalDefaults['display_size'][0] *
                        GlobalDefaults['scale'][0],
                        scaled_size[1] / GlobalDefaults['display_size'][1] *
                        GlobalDefaults['scale'][1]]

        MyWindow.small_win = visual.Window(units='pix',
                                           colorSpace='rgb',
                                           winType='pyglet',
                                           allowGUI=True,
                                           color=GlobalDefaults['background'],
                                           size=scaled_size,
                                           pos=[0, 0],
                                           fullscr=False,
                                           # viewPos=GlobalDefaults['offset'],
                                           viewScale=scaled_scale,
                                           screen=0,
                                           waitBlanking=False,
                                           do_vsync=False)

    @staticmethod
    def flip():
        """Makes proper calls to flip windows
        """
        if MyWindow.win is not None:
            MyWindow.win.flip()

            if MyWindow.small_win is not None:
                MyWindow.small_win.flip()

    @staticmethod
    def send_trigger():
        """Triggers recording device by sending short voltage spike from LabJack
        U3-HV. Spike lasts approximately 0.4 ms if connected via high speed USB
        (2.0). Ensure high enough sampling rate to reliably detect triggers.
        Set to use flexible IO #4 (FIO4).
        """
        if has_u3:
            try:
                # voltage spike; 0 is low, 1 is high, on flexible IO #4
                MyWindow.d.setFIOState(4, 1)
                # reset
                MyWindow.d.setFIOState(4, 0)
            except Exception as e:
                print 'Triggering Error:',
                print str(e)

        else:
            print '\nTo trigger, need labjackpython library. See documentation'


class StimDefaults(object):
    """Super class to hold parameter defaults. GUI passes dictionary of all
    parameters, whether used to make stim or not.

    :param string shape: Shape of the stim, 'circle', 'rectangle, or 'annulus'.

    :param string fill_mode: How the stim is filled. Can be 'uniform',
     'sine', 'square', 'concentric', 'checkerboard', 'random', 'image',
     or 'movie'.

    :param float orientation: Orientation of the stim, in degrees.

    :param list size: Size of the stim, as an x, y list.

    :param float outer_diameter: Size of circle, or outer diameter of
     annulus, in micrometers.

    :param float inner_diameter: Inner diameter of annulus, in micrometers.

    :param list check_size: Size of each check in a checkerboard or randomly
     filled board, as an x, y list in micrometers.

    :param int num_check: The number of checks in each direction.

    :param float delay: The time to between the first frame and the stim
     appearing on screen. Rounds up to the nearest frame.

    :param float end_delay: The time to between the last frame stim
     appearing on screen and the end of frames flipping. Rounds up to the
     nearest frame.

    :param float duration: The duration for which the stim will animated.
     Rounds up to the nearest frame.

    :param list location: Coordinates of the stim, as an x, y list.

    :param string timing: How the stim appears on screen over time. For
     'step', the stim appears immediately. Other options include 'sine',
     'sawtooth', 'square', and 'linear'.

    :param float period_mod: For cyclic timing modes, the number of cycles.

    :param float alpha: The transparency of the of the stim, between 0 and 1.
     Does not apply to checkerboard or random fill stims, or images and movies.

    :param string color_mode: The way in which the color of the stim is
     determined. Can be either 'intensity', or 'rgb'.

    :param string contrast_channel: The color channel in which color is
     displayed in intensity mode. For the RGB color mode, contrast channel is
     only used if a fill other than uniform is specified.

    :param float intensity: The color of the stim relative to background,
     between -1 and 1. For  fills, the color will fluctuate between high and
     low values of the  specified intensity relative to background, and thus
     background values on either extreme must use low intensities or risk
     hitting the color ceiling/floor of the monitor.

    :param list color: RGB color values of the stim, as a list of 3 values
     between -1 and 1.

    :param float fill_seed: The seed for the random number generator for
     random fills.

    :param float move_seed: The seed for the random number generator for
     random movement.

    :param float speed: The speed of moving stims, in micrometers per second.

    :param int num_dirs: The number of directions radially moving stims will
     travel in.

    :param float start_dir: The start direction for radially moving stims.

    :param float start_radius: The start radius for radially moving stims.

    :param float move_delay: The amount of wait time between each move
     direction.

    :param float travel_distance: The distance that randomly moving stims
     will travel before choosing a new direction.

    :param float sf: The spatial frequency of a stim texture.

    :param list phase: The offset of texture in the stim. Units are in
     cycles, so integer phases will result in no discernible change.

    :param string movie_filename: File path of the movie to be displayed.

    :param list movie_size: Size of the movie, as an x, y list, in micrometers.
     Keep aspect ratio or movie will be distorted.

    :param string image_filename: File path of the image to be displayed.

    :param list image_size: Size of the image, as an x, y list, in micrometers.
     Keep aspect ratio or movie will be distorted.

    :param string table_filename: File path of the table to be used for
     coordinates.

    :param bool trigger: Whether or not to send a trigger for the stim.

    :param int num_jumps:

    :param float jump_delay:

    :param float force_stop: time at which stim should end, overrides all
     other timing. Useful for moving and table stims.
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
                 check_type='board',
                 delay=0,
                 duration=0.5,
                 location=None,
                 timing='step',
                 intensity=1,
                 alpha=1,
                 color=None,
                 color_mode='intensity',
                 image_channel='all',
                 fill_seed=1,
                 move_seed=1,
                 speed=10,
                 num_dirs=4,
                 start_dir=0,
                 start_radius=300,
                 travel_distance=50,
                 ori_with_dir=False,
                 intensity_dir='both',
                 sf=1,
                 phase=None,
                 phase_speed=None,
                 contrast_channel='green',
                 movie_filename=None,
                 movie_size=None,
                 period_mod=1,
                 image_size=None,
                 image_filename=None,
                 table_filename=None,
                 table_type='polar',
                 trigger=False,
                 move_delay=0,
                 num_jumps=5,
                 # jump_delay=None,
                 shuffle=False,
                 blend_jumps=False,
                 force_stop=0,
                 end_delay=0,
                 **kwargs):
        """
        Default variable constructors; distance and time units converted
        appropriately.
        """
        for key, value in kwargs.iteritems():
            print 'NOT USED: {}={}'.format(key, value)

        self.shape = shape
        self.fill_mode = fill_mode
        self.sf = sf
        self.intensity_dir = intensity_dir
        self.color_mode = color_mode
        self.intensity = intensity
        self.alpha = alpha
        self.orientation = orientation
        self.num_check = num_check
        self.check_type = check_type
        self.fill_seed = fill_seed
        self.timing = timing
        self.period_mod = period_mod * 2.0 * duration
        self.move_seed = move_seed
        self.num_dirs = num_dirs
        self.ori_with_dir = ori_with_dir
        self.movie_filename = movie_filename
        self.image_filename = image_filename
        self.table_filename = table_filename
        self.table_type = table_type
        self.trigger = trigger
        self.num_jumps = num_jumps
        self.shuffle = shuffle
        self.blend_jumps = blend_jumps

        self.contrast_channel = ['red', 'green', 'blue'].\
            index(contrast_channel)
        self.image_channel = ['red', 'green', 'blue', 'all'].\
            index(image_channel)

        # override start dir with global
        if GlobalDefaults['pref_dir'] != -1:
            self.start_dir = GlobalDefaults['pref_dir']
        else:
            self.start_dir = start_dir

        # mutable variables
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
            self.phase = [0, 0]

        # size conversions
        self.outer_diameter = outer_diameter * GlobalDefaults['pix_per_micron']
        self.inner_diameter = inner_diameter * GlobalDefaults['pix_per_micron']
        self.start_radius = start_radius * GlobalDefaults['pix_per_micron']
        self.travel_distance = travel_distance * GlobalDefaults[
            'pix_per_micron']

        # time conversions
        self.delay = delay * GlobalDefaults['frame_rate']
        self.end_delay = end_delay * GlobalDefaults['frame_rate']
        self.duration = duration * GlobalDefaults['frame_rate']
        self.move_delay = int(move_delay * GlobalDefaults['frame_rate'])
        # self.jump_delay = jump_delay * GlobalDefaults['frame_rate']
        self.force_stop = force_stop * GlobalDefaults['frame_rate']

        # speed conversion
        self.speed = speed * (1.0 * GlobalDefaults['pix_per_micron'] /
                              GlobalDefaults['frame_rate'])

        # mutable variables with unit conversion
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
            self.movie_size = [movie_size[0] * GlobalDefaults[
                'pix_per_micron'],
                               movie_size[1] * GlobalDefaults[
                'pix_per_micron']]
        else:
            self.movie_size = [100, 100]

        if image_size is not None:
            self.image_size = map(int,
                                  [image_size[0] *
                                   GlobalDefaults['pix_per_micron'],
                                   image_size[1] *
                                   GlobalDefaults['pix_per_micron']])
        else:
            self.movie_size = [100, 100]

        if check_size is not None:
            self.check_size = [check_size[0] * GlobalDefaults[
                'pix_per_micron'],
                               check_size[1] * GlobalDefaults[
                'pix_per_micron']]
        else:
            self.check_size = [100, 100]

        if phase_speed is not None:
            self.phase_speed = [phase_speed[0] * 1.0 / GlobalDefaults[
                'frame_rate'], phase_speed[1] * 1.0 / GlobalDefaults[
                'frame_rate']]
        else:
            self.phase_speed = [0, 0]


class StaticStim(StimDefaults):
    """Class for generic non moving stims. Super class for other stim
    types. Stim object instantiated in :py:func:`.make_stim`, and drawn with
    calls to animate().
    """
    def __init__(self, **kwargs):
        """Passes parameters up to super class. Seeds randoms.
        """
        # pass parameters up to super
        super(StaticStim, self).__init__(**kwargs)

        # non parameter instance attributes
        self.start_stim = None
        self.end_stim = None
        self.draw_duration = None
        self.stim = None
        self.small_stim = None
        self.contrast_adj_rgb = None

        # seed fill and move randoms
        self.fill_random = Random()
        self.fill_random.seed(self.fill_seed)
        self.move_random = Random()
        self.move_random.seed(self.move_seed)

    def make_stim(self):
        """Creates instance of psychopy stim object.
        """
        self.stim = visual.GratingStim(win=MyWindow.win,
                                       size=self.gen_size(),
                                       mask=self.gen_mask(),
                                       tex=self.gen_texture(),
                                       pos=self.location,
                                       phase=self.phase,
                                       ori=self.orientation,
                                       autoLog=False,
                                       texRes=2**10)

        self.stim.sf *= self.sf

        if MyWindow.small_win is not None:
            self.small_stim = visual.GratingStim(win=MyWindow.small_win,
                                                 size=self.stim.size,
                                                 mask=self.stim.mask,
                                                 tex=self.stim.tex,
                                                 pos=self.location,
                                                 phase=self.phase,
                                                 ori=self.orientation,
                                                 autoLog=False)

            self.small_stim.sf *= self.sf

    def draw_times(self):
        """Determines during which frames stim should be drawn, based on desired
        delay and duration times.

        :return: last frame number as int
        """
        # round up
        self.start_stim = int(ceil(self.delay))

        if self.trigger:
            if self.start_stim not in MyWindow.frame_trigger_list:
                MyWindow.frame_trigger_list.add(self.start_stim)

        self.end_stim = int(ceil(self.duration + self.start_stim))
        self.end_delay = int(ceil(self.end_delay))

        self.draw_duration = self.end_stim - self.start_stim

        if self.force_stop != 0:
            self.end_stim = int(ceil(self.force_stop))
            self.end_delay = 0

        return self.end_stim + self.end_delay

    def animate(self, frame):
        """Method for drawing stim objects to back buffer. Checks if object
        should be drawn. Back buffer is brought to front with calls to flip()
        on the window.

        :param int frame: current frame number
        """
        # check if within animation range
        if self.start_stim <= frame < self.end_stim:
            # adjust colors and phase based on timing
            if self.fill_mode not in ['movie', 'image'] and self.timing != \
                    'step':
                self.gen_timing(frame)

            if self.fill_mode != 'movie':
                self.gen_phase()

            # draw to back buffer
            self.stim.draw(MyWindow.win)

            if self.small_stim is not None:
                self.small_stim.draw(MyWindow.small_win)

    def gen_rgb(self):
        """Depending on color mode, calculates necessary values. Texture
        color is either relative to background by specifying intensity in a
        certain channel, or passed as RGB values by the user.

        :return: tuple of high, low, delta, and background
        """
        background = GlobalDefaults['background']
        # scale from (-1, 1) to (0, 1), for math and psychopy reasons
        background = (numpy.array(background, dtype='float') + 1) / 2
        background = background[self.contrast_channel]

        if self.color_mode == 'rgb':
            # scale
            high = (numpy.array(self.color, dtype='float') + 1) / 2
            low = (numpy.array(GlobalDefaults['background'], dtype='float') +
                   1) / 2

            # append alpha
            high = numpy.append(high, self.alpha)
            low = numpy.append(low, self.alpha)

            delta = (high[self.contrast_channel] - low[self.contrast_channel])

            color = high, low, delta, background

        elif self.color_mode == 'intensity':

            # get change relative to background
            delta = background * self.intensity

            # get high and low
            high = background + delta
            low = background - delta

            # if single direction, bring middle up to halfway between high
            # and background
            if self.intensity_dir == 'single':
                low += delta
                delta /= 2
                background += delta

            # unscale high/low (only used by board texture)
            high = high * 2.0 - 1
            low = low * 2.0 - 1

            color = high, low, delta, background

        return color

    def gen_size(self):
        """Calculates sizes of various sims.

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
        """Determines the mask of the stim object. The mask determines the
        shape of the stim. See psychopy documentation for more details.

        :return: mask of the stim object, as a string
        """
        if self.shape in ['circle', 'annulus']:
            stim_mask = 'circle'

        elif self.shape == 'rectangle':
            stim_mask = None

        return stim_mask

    def gen_texture(self):
        """Generates texture for stim object. Textures are 3D numpy arrays
        (size*size*4). The 3rd dimension is RGB and Alpha (transparency)
        values.

        :return: texture as numpy array
        """

        # make array
        size = (max(self.gen_size()),) * 2  # square tuple of largest size
        # not needed for images
        if self.fill_mode != 'image':
            # make black rgba array, set alpha
            texture = numpy.full(size + (4,), -1, dtype=numpy.float)
            texture[:, :, 3] = self.alpha

        high, low, delta, background = self.gen_rgb()

        if self.fill_mode == 'uniform':
            if self.color_mode == 'rgb':
                # unscale
                color = high * 2 - 1
                # color array
                texture[:, :, ] = color
            elif self.color_mode == 'intensity':
                # adjust
                color = background + delta
                # unscale
                color = color * 2 - 1
                # color array
                texture[:, :, self.contrast_channel] = color

        elif self.fill_mode == 'sine':
            # adjust color
            color = (filters.makeGrating(size[0], gratType='sin',
                                         cycles=1)) * delta + background
            # unscale
            color = color * 2 - 1
            # color array
            texture[:, :, self.contrast_channel] = color

        elif self.fill_mode == 'square':
            # adjust color
            color = (filters.makeGrating(size[0], gratType='sqr',
                                         cycles=1)) * delta + background
            # unscale
            color = color * 2 - 1
            # color array
            texture[:, :, self.contrast_channel] = color

        elif self.fill_mode == 'concentric':
            # adjust color
            color = scipy.sin(filters.makeRadialMatrix(size[0]) * 2 - 1) * \
                delta + background
            # unscale
            color = color * 2 - 1
            # color array
            texture[:, :, self.contrast_channel] = color

        elif self.fill_mode == 'image':
            # get pic from file
            try:
                pic_name = os.path.basename(self.image_filename)
            except TypeError:
                raise IOError('Make sure image exists and location is correct')

            filename, file_ext = os.path.splitext(pic_name)

            if file_ext != '.iml':
                image = Image.open(self.image_filename)

                # make smaller for faster correction if possible
                if max(image.size) > max(self.gen_size()):
                    image.thumbnail(self.gen_size(), Image.ANTIALIAS)

                # rescale rgb
                texture = numpy.asarray(image) / 255.0 * 2 - 1

                # if only want one color channel, remove others
                if self.image_channel != 3:
                    for i in range(3):
                        if self.image_channel != i:
                            texture[:, :, i] = -1

                # add alpha
                texture = numpy.insert(texture, 3, self.alpha, axis=2)

            # if .iml
            else:
                image = numpy.fromfile(self.image_filename, dtype='uint16')
                image.byteswap(True)  # changes endianness
                image = image.reshape(1024, 1536)

                maxi = image.max()
                if maxi <= 4095:
                    maxi = 4095

                image = image.astype(numpy.float64)

                image /= maxi

                if self.image_channel != 3:
                    texture = numpy.zeros((1024, 1536, 3))
                    texture[:, :, self.image_channel] = image

                    texture *= 2
                    texture -= 1

                    # add alpha values
                    texture = numpy.insert(texture, 3, self.alpha, axis=2)

                # .iml are gray scale by default
                else:
                    image *= 2
                    image -= 1
                    texture = image

            texture = numpy.rot90(texture, 2)

        # gamma correct
        if MyWindow.gamma_mon is not None:
            texture = MyWindow.gamma_mon(texture)

        # make center see through if annuli
        if self.shape == 'annulus':
            radius = filters.makeRadialMatrix(self.outer_diameter,
                                              radius=1.0 / self.outer_diameter)
            texture[numpy.where(radius < self.inner_diameter)] = [0, 0, 0, -1]

        return texture

    def gen_timing(self, frame):
        """Adjusts color values of stims based on desired timing in desired
        channel(i.e. as a function of current frame over draw time).
        Recalculated on every call to animate()

        TODO: precompute values

        :param frame: current frame number
        :return: list of rgb values as floats
        """
        stim_frame_num = frame - self.start_stim
        time_fraction = stim_frame_num * 1.0 / self.draw_duration
        texture = self.stim.tex

        _, _, delta, background = self.gen_rgb()

        if self.timing == 'sine':
            # adjust color
            if self.intensity_dir == 'both':
                color = scipy.sin(self.period_mod * scipy.pi *
                                  time_fraction) * delta + background

            elif self.intensity_dir == 'single':
                color = scipy.sin(self.period_mod * scipy.pi *
                                  time_fraction - scipy.pi / 2) * delta + \
                    background

        elif self.timing == 'square':
            if self.intensity_dir == 'both':
                color = (scipy.signal.square(self.period_mod * scipy.pi *
                                             time_fraction, duty=0.5) * 2) / \
                    2 * delta + background

            if self.intensity_dir == 'single':
                color = scipy.signal.square(self.period_mod * scipy.pi *
                                            time_fraction, duty=0.5) * delta \
                    + background

        elif self.timing == 'sawtooth':
            if self.intensity_dir == 'both':
                color = (scipy.signal.sawtooth(self.period_mod * scipy.pi *
                                               time_fraction, width=0.5) * 2) \
                    / 2 * delta + background

            if self.intensity_dir == 'single':
                color = scipy.signal.sawtooth(self.period_mod * scipy.pi *
                                              time_fraction, width=0.5) * \
                    delta + background

        elif self.timing == 'linear':
            # if self.intensity_dir == 'both':
            color = background + delta * (time_fraction * 2 - 1)

            # if self.intensity_dir == 'single':
            #     color = background + delta * time_fraction

        # unscale
        color = color * 2 - 1

        # gamma correct
        if MyWindow.gamma_mon is not None and self.fill_mode not in ['image']:
            color = MyWindow.gamma_mon(color, channel=self.contrast_channel)

        texture[:, :, self.contrast_channel] = color

        self.stim.tex = texture

        if self.small_stim is not None:
            self.small_stim.tex = texture

    def gen_phase(self):
        """Changes phase of stim on each frame draw.
        """
        if any(self.phase_speed):
            self.stim.phase += (self.phase_speed[0], self.phase_speed[1])

    def set_rgb(self, rgb):
        """Color setter.

        :param rgb: tuple or list of rgb values
        """
        self.stim.setColor(rgb)


class MovingStim(StaticStim):
    """Class for stims moving radially inwards. Overrides several methods.
    """

    def __init__(self, **kwargs):
        """Passes parameters up to super class.
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
        self.error_count = 0

        # to track random motion positions
        self.log = [[], [0], []]  # angle, frame num, position

    def draw_times(self):
        """Determines during which frames stim should be drawn, based on desired
        delay and duration times. Overrides super method.

        :return: last frame number as int
        """
        self.start_stim = int(self.delay + 0.99)

        # need to generate movement to get number of frames
        self.gen_pos()

        self.end_stim = self.num_frames * self.num_dirs
        self.end_stim += self.start_stim
        self.end_stim = int(self.end_stim + 0.99)
        self.end_delay = int(self.end_delay + 0.99)

        self.draw_duration = self.end_stim - self.start_stim

        if self.trigger:
            for x in range(self.num_dirs):
                trigger_frame = self.num_frames * x + self.start_stim
                if trigger_frame not in MyWindow.frame_trigger_list:
                    MyWindow.frame_trigger_list.add(trigger_frame)

        if self.force_stop != 0:
            self.end_stim = self.force_stop
            self.end_delay = 0

        return self.end_stim + self.end_delay

    def animate(self, frame):
        """Method for animating moving stims. Moves stims appropriately,
        then makes call to animate of super.

        :param frame: current frame number
        """
        # check if within animation range
        if self.start_stim <= frame < self.end_stim:
            # if next coordinate is calculated, moves stim, otherwise calls
            # gen_movement() and retries
            try:
                x, y = self.get_next_pos()
                self.set_pos(x, y)

                super(MovingStim, self).animate(frame)

                # to raise errors to stop recursion
                self.error_count = 0

            except (AttributeError, IndexError, TypeError):
                self.error_count += 1
                if self.error_count == 2:
                    raise

                # make new coordinate array
                # TODO: don't generate on the fly
                self.gen_pos()

                # log frame number for RandomlyMovingStim
                self.log[1].append(frame)

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

        # orient shape if not an image and fill is uniform
        if self.ori_with_dir:
            self.stim.ori = self.start_dir + self.orientation

        # set start_dir for next call of gen_pos()
        self.start_dir += 360 / self.num_dirs

        # start_dir cannot be more than 360
        if self.start_dir >= 360:
            self.start_dir -= 360

        # add to log
        self.log[0].append(angle)
        self.log[2].append(self.get_pos())

        # calculate variables
        travel_distance = ((self.current_x**2 + self.current_y**2) ** 0.5) * 2
        self.num_frames = int(travel_distance / self.speed + 0.99)  # round up

        # generate position array
        self.x_array, self.y_array = self.gen_pos_array(self.current_x,
                                                        self.current_y,
                                                        self.num_frames,
                                                        angle)

        # add in move delay by placing stim off screen
        if self.move_delay > 0:
            if len(self.stim.size) > 1:
                max_size = max(self.stim.size)
            else:
                max_size = self.stim.size

            off_x = (GlobalDefaults['display_size'][0] + max_size) / 2
            off_y = (GlobalDefaults['display_size'][1] + max_size) / 2

            for i in xrange(self.move_delay):
                self.x_array = scipy.append(self.x_array, off_x)
                self.y_array = scipy.append(self.y_array, off_y)

            self.num_frames += self.move_delay

    def gen_start_pos(self, direction):
        """Calculates starting position in x, y coordinates on the starting
        radius based on travel direction.

        :param direction: starting position on border of frame based on travel
        :return: starting position on border of frame based on travel angle
         origin
        """
        start_x = self.start_radius * scipy.sin(direction * scipy.pi / 180)
        start_y = self.start_radius * scipy.cos(direction * scipy.pi / 180)

        return start_x, start_y

    def gen_pos_array(self, start_x, start_y, num_frames, angle):
        """Creates 2 arrays for x, y coordinates of stims for each frame.

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
        """Returns the next coordinate from x, y_array for animate to set the
        position of the stim for the next frame.

        :return: x, y coordinate as tuple
        """
        x = self.x_array[self.frame_counter]
        y = self.y_array[self.frame_counter]

        # increment frame counter for next frame
        self.frame_counter += 1

        return x, y

    def set_pos(self, x, y):
        """Position setter. Necessary for alternate position setting in subclasses.

        :param x: x coordinate
        :param y: y coordinate
        """
        self.stim.setPos((x, y))
        if self.small_stim is not None:
            self.small_stim.setPos((x, y))

    def get_pos(self):
        """Position getter.
        """
        return self.stim.pos


class RandomlyMovingStim(MovingStim):
    """Class for stims moving randomly. Overrides several classes.
    """

    def __init__(self, **kwargs):
        """Passes parameters up to super class.
        """
        # pass parameters up to super
        super(RandomlyMovingStim, self).__init__(**kwargs)

    def draw_times(self):
        """Determines during which frames stim should be drawn, based on desired
        delay and duration times.

        :return: last frame number as int
        """
        self.gen_pos()

        self.end_stim = super(MovingStim, self).draw_times() - self.end_delay

        if self.trigger:
            for x in xrange(int(self.duration / self.num_frames + 0.99)):
                trigger_frame = self.num_frames * x + self.start_stim
                if trigger_frame not in MyWindow.frame_trigger_list:
                    MyWindow.frame_trigger_list.add(trigger_frame)

        return self.end_stim + self.end_delay

    def gen_pos(self):
        """Makes calls to :py:func:`gen_start_pos` and
        :py:func:`gen_pos_array` with proper variables to get new array of
        position coordinates. Overrides super.
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
    """Class where stim motion is determined by a table of radial coordinates.

    Table can be a text file with tab or space separated values and newlines
    between rows, or an Igor file in binary wave/packed experiment format.
    Trigger will occur right before frame where indicated position is
    flipped. First and last coordinate will always trigger (if stim is set to
    trigger).

    For a binary wave file, accepted formats are polar and coordinate,
    and triggering will only happen on first coordinate. For packed
    experiment files, leave wave names as 'wave0' and 'wave1', where 'wave0'
    is coordinates and 'wave1' is whether or not to trigger (if polar),
    or as 'wave0', 'wave1', 'wave2' (if xy).

    There are 3 table types: polar, coordinate, or direction. Their formats
    are as follows.

    Polar: Tab or space separated values. Each line must include both a
    radius, and then whether or not to trigger for that frame (as a 0 or 1).

    Coordinate: Tab or space separated values. Each line must include an x
    coordinate, a y coordinate, and whether or not to trigger (as 0 or 1).

    Direction: Tab or space separated values. Each line must include a
    movement speed (pix/sec), a duration (ms), and a direction in degrees.
    Optionally, direction can be replaced with '$' (dollar sign), and the
    direction will default to the global default (can also do use '-$').
    """
    def __init__(self, **kwargs):
        """Passes parameters up to super."""
        super(TableStim, self).__init__(**kwargs)

        # instance attributes
        self.trigger_frames = None

    def draw_times(self):
        """Determines during which frames stim should be drawn, based on desired
        delay and duration times. Overrides super method.

        :return: last frame number as int
        """

        self.start_stim = self.delay

        # need to generate movement to get number of frames
        self.gen_pos()

        self.end_stim = self.num_frames * self.num_dirs
        self.end_stim += self.start_stim
        self.end_stim = int(self.end_stim + 0.99)

        self.draw_duration = self.end_stim - self.start_stim

        if self.trigger_frames is not None:
            if self.trigger:
                for j in range(self.num_dirs):
                    for i in self.trigger_frames:
                        trigger_frame = i + j * self.num_frames
                        if trigger_frame not in MyWindow.frame_trigger_list:
                            MyWindow.frame_trigger_list.add(trigger_frame)

        if self.force_stop != 0:
            self.end_stim = self.force_stop

        return self.end_stim

    def gen_pos(self):
        """Overrides super method. Calls gen_pos_array() and resets frame
        counter.
        """
        self.frame_counter = 0
        self.x_array, self.y_array = self.gen_pos_array()

        # orient shape if not an image and fill is uniform
        if self.ori_with_dir:
            self.stim.ori = self.start_dir + self.orientation

        # add in move delay by placing stim off screen
        if len(self.stim.size) > 1:
            max_size = max(self.stim.size)
        else:
            max_size = self.stim.size

        off_x = (GlobalDefaults['display_size'][0] + max_size) / 2
        off_y = (GlobalDefaults['display_size'][1] + max_size) / 2

        for i in xrange(self.move_delay):
            self.x_array = scipy.append(self.x_array, off_x)
            self.y_array = scipy.append(self.y_array, off_y)

        self.num_frames += self.move_delay

        # set start_dir for next call of gen_pos()
        self.start_dir += 360 / self.num_dirs

        # start_dir cannot be more than 360
        if self.start_dir >= 360:
            self.start_dir -= 360

    def gen_pos_array(self, *args):
        """Creates 2 arrays for x, y coordinates of stims for each frame.

        :return: the x, y coordinates of the stim for every frame as 2 arrays
        :raises ImportError: if attempts to load from an Igor file without
         having the igor module.
        :raises IOError: raised if file contents not properly formatted.
        """
        table = self.table_filename
        radii = None
        x = None

        if table is None:
            raise IOError('No table file selected')

        if not os.path.exists(table):
            raise IOError('No such table file: {}'.format(table))

        # if text file
        if os.path.splitext(table)[1] == '.txt':
            with open(table, 'r') as f:
                lines = [line.strip() for line in f]

            if self.table_type == 'polar':
                radii = [i.split()[0] for i in lines]
                trigger_list = [i.split()[1] for i in lines]

            elif self.table_type == 'coordinate':
                x = [i.split()[0] for i in lines]
                y = [i.split()[1] for i in lines]
                try:
                    trigger_list = [i.split()[2] for i in lines]
                except IndexError:
                    raise IOError('File contents not a supported format. See '
                                  'docs for reference. Selected file: {}.'.
                                  format(self.table_filename))

            elif self.table_type == 'directions':

                x = numpy.array([])
                y = numpy.array([])
                trigger_list = []

                for line in lines:
                    if len(x) == 0:
                        start_x = self.location[0]
                        start_y = self.location[1]
                    else:
                        start_x = x[-1]
                        start_y = y[-1]

                    speed = float(line.split()[0])
                    dur = float(line.split()[2]) / 1000  # convert ms to sec
                    try:
                        dir = float(line.split()[1])
                    except ValueError:
                        if line.split()[1] == '$':
                            if GlobalDefaults['pref_dir'] != -1:
                                dir = GlobalDefaults['pref_dir'] + 180
                            elif GlobalDefaults['pref_dir'] == -1:
                                dir = 0
                        elif line.split()[1] == '-$':
                            if GlobalDefaults['pref_dir'] != -1:
                                dir = GlobalDefaults['pref_dir']
                            elif GlobalDefaults['pref_dir'] == -1:
                                dir = 0

                    num_frames = int(GlobalDefaults['frame_rate'] * dur + 0.99)
                    trigger_list.append(1)
                    trigger_list.extend([0] * (num_frames - 1))
                    self.speed = speed * (1.0 / GlobalDefaults['frame_rate'])

                    x_to_app, y_to_app = super(TableStim,
                                               self).gen_pos_array(start_x,
                                                                   start_y,
                                                                   num_frames,
                                                                   dir)

                    x = numpy.append(x, x_to_app)
                    y = numpy.append(y, y_to_app)

            trigger_list[0] = 1   # trigger on first frame
            trigger_list[-1] = 1  # trigger on last frame

        # if igor binary wave format or packed experiment format
        elif os.path.splitext(table)[1] in ['.ibw', '.pxp']:
            if has_igor:
                if os.path.splitext(table)[1] == '.ibw':
                    if self.table_type == 'polar':
                        radii = binarywave.load(table)['wave']['wData']
                    else:
                        raise IOError('.ibw format does not support '
                                      'coordinate table type')

                elif os.path.splitext(table)[1] == '.pxp':
                    if self.table_type == 'polar':
                        radii = packed.load(table)[1]['root']['wave0'].wave[
                            'wave']['wData']
                        trigger_list = packed.load(table)[1]['root'][
                            'wave1'].wave['wave']['wData']

                    if self.table_type == 'coordinate':
                        x = packed.load(table)[1]['root']['wave0'].wave[
                            'wave']['wData']
                        y = packed.load(table)[1]['root']['wave1'].wave[
                            'wave']['wData']
                        trigger_list = packed.load(table)[1]['root'][
                            'wave2'].wave['wave']['wData']

                    trigger_list[0] = 1   # trigger on first frame
                    trigger_list[-1] = 1  # trigger on last frame

            elif not has_igor:
                raise ImportError('Need igor python module to load \'.ibw\' '
                                  'or \'.pxp\' formats. Install module with '
                                  '\'pip install igor\'.')

        # convert strings to floats, and convert to pix to micrometers
        if radii is not None:
            radii = map(float, radii)
            radii = [r * GlobalDefaults['pix_per_micron'] for r in radii]
        elif x is not None:
            x = map(float, x)
            y = map(float, y)
            x = [i * GlobalDefaults['pix_per_micron'] for i in x]
            y = [i * GlobalDefaults['pix_per_micron'] for i in y]
        else:
            raise IOError('File contents not a supported format. See docs for '
                          'reference. Selected file: {}.'.
                          format(self.table_filename))

        if trigger_list is not None:
            trigger_list = map(int, trigger_list)
            self.trigger_frames = []

            for i in xrange(len(trigger_list)):
                if trigger_list[i] == 1:
                    self.trigger_frames.append(i)

        self.num_frames = len(radii) if radii is not None else len(x)

        # make arrays if polar
        if self.table_type == 'polar':
            theta = self.start_dir * -1 - 90  # origins are different in cart
            x, y = map(list, zip(*[pol2cart(theta, r) for r in radii]))

        return x, y


class ImageJumpStim(StaticStim):
    """Class to jump through random areas on a larger image.

    Currently broken.
    """
    def __init__(self, **kwargs):
        # pass parameters up to super
        super(ImageJumpStim, self).__init__(**kwargs)

        self.orig_tex = None
        self.slice_index = 0
        self.slice_list = []
        self.slice_log = []
        self.jumpstim_list = []

    def gen_texture(self):
        """
        Keeps copy of og texture
        :return:
        """
        mock_jump = StaticStim(image_filename=self.image_filename,
                               image_channel=['red', 'green', 'blue', 'all'][
                                   self.image_channel],
                               image_size=self.image_size,
                               fill_mode='image',
                               shape=self.shape)

        tex = mock_jump.gen_texture()

        MyWindow.close_win()
        cap_win = visual.Window(units='pix', size=self.image_size)

        mock_stim = visual.GratingStim(win=cap_win,
                                       size=self.image_size,
                                       mask=None,
                                       tex=tex,
                                       autoLog=False)
        mock_stim.draw()
        tex = cap_win._getRegionOfFrame(buffer='back')
        cap_win.close()
        MyWindow.make_win()
        cap = numpy.asarray(tex.transpose(Image.FLIP_TOP_BOTTOM))
        cap = uint8_float(cap)

        self.orig_tex = cap

        self.gen_slice_list()

        # Pushing textures is slow, but preloading textures is memory
        # expensive. Generating shuffled textures is too slow, so preload
        # those, but do other slices on the fly.

        numpy.random.seed(self.move_seed)
        # clock = core.Clock()

        if self.shuffle:
            for i, slice in enumerate(tqdm(self.slice_list)):
                temp_stim = visual.GratingStim(win=MyWindow.win,
                                               size=self.gen_size(),
                                               mask=self.gen_mask(),
                                               tex=slice,
                                               pos=self.location,
                                               phase=self.phase,
                                               ori=self.orientation,
                                               autoLog=False,
                                               texRes=2**10)

                # want to shuffle scaled tex, so draw to back and pull, then
                # shuffle that
                temp_stim.draw()
                image = MyWindow.win._getRegionOfFrame(buffer='back')
                MyWindow.win.clearBuffer()
                cap = numpy.asarray(image) / 255.0 * 2 - 1

                if self.image_channel != 3:
                    numpy.random.shuffle(cap.reshape(-1, cap.shape[-1])
                                         .T[self.image_channel])
                else:
                    # TODO: faster randomizing
                    numpy.random.shuffle(cap.reshape(-1, cap.shape[-1]))

                # slice = cap
                temp_stim.setTex(cap)
                self.jumpstim_list.append(temp_stim)

        return tex

    def gen_size(self):
        """
        Overrides sizing
        :return:
        """
        size = [GlobalDefaults['display_size'][0],
                GlobalDefaults['display_size'][1]]

        return size

    def draw_times(self):
        """
        Determines frames during which to draw stimulus.
        :return: last frame number as int
        """

        self.start_stim = self.delay

        self.end_stim = self.num_jumps * self.move_delay
        self.end_stim += self.start_stim
        self.end_stim = int(self.end_stim + 0.99)

        self.draw_duration = self.end_stim - self.start_stim

        if self.trigger:
            for i in range(self.num_jumps + 1):
                trigger_frame = i * self.move_delay + self.delay
                if trigger_frame not in MyWindow.frame_trigger_list:
                    MyWindow.frame_trigger_list.add(trigger_frame)

        if self.force_stop != 0:
            self.end_stim = self.force_stop

        return self.end_stim

    def animate(self, frame):
        """Method for animating moving stims. Pulls pixels drawn,
        then makes call to animate of super.

        :param frame: current frame number
        """
        # check if within animation range
        # clock = core.Clock()
        # clock.reset()
        if self.start_stim <= frame < self.end_stim:

            if frame % self.move_delay == 0:
                if self.shuffle:
                    self.stim = self.jumpstim_list[self.slice_index]
                else:
                    self.stim.setTex(self.slice_list[self.slice_index])

                    if self.small_stim is not None:
                        self.small_stim.setTex(self.slice_list[
                                               self.slice_index])

                self.slice_index += 1

            super(ImageJumpStim, self).animate(frame)

        # print clock.getTime() * 1000

    def gen_slice(self, *args):
        """Slices the original texture and returns slice, i.e. a smaller
        section of the original image that will be zoomed in.

        :return: texture slice
        """
        if self.image_size[0] >= GlobalDefaults['display_size'][0] and \
                self.image_size[1] >= GlobalDefaults['display_size'][1]:

            x = int(GlobalDefaults['display_size'][0])
            y = int(GlobalDefaults['display_size'][1])

            # maximum coordinate of slice
            max_x = self.orig_tex.shape[1] - x
            max_y = self.orig_tex.shape[0] - y

            x_low = self.move_random.randint(0, max_x)
            y_low = self.move_random.randint(0, max_y)

            x_high = int(x_low + x)
            y_high = int(y_low + y)

            self.slice_log.append([y_low, y_high, x_low, x_high])

            # subsection of original 1536x1024 image of window size
            tex = self.orig_tex[y_low:y_high,
                                x_low:x_high]

            return tex

        else:
            raise AssertionError('Image drawn size must be larger than window '
                                 'size (can\'t jump around otherwise...).'
                                 '\nImage size:  {} x {} pixels'
                                 '\nwindow size: {} x {} pixels'.format(
                                     self.image_size[0],
                                     self.image_size[1],
                                     GlobalDefaults['display_size'][0],
                                     GlobalDefaults['display_size'][1]))

    def gen_slice_list(self):
        """
        Generates slices for jumping around.
        """
        for i in trange(self.num_jumps):
            self.slice_list.append(self.gen_slice())


# function because inheritance is conditional
def board_texture_class(bases, **kwargs):

    class BoardTexture(bases):
        """Class for checkerboard or random board textures. Rather than grating
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
            """Creates instance of psychopy stim object.
            """
            # array of coordinates for each element
            xys = []
            # populate xys
            for y in xrange(self.num_check / -2, self.num_check / 2):
                for x in xrange(self.num_check / -2, self.num_check / 2):
                    xys.append((self.check_size[0] * x,
                                self.check_size[1] * y))

            # get colors
            high, low, _, _ = self.gen_rgb()
            # print high, low
            self.high = high
            self.low = low

            # array of rgbs for each element (2D)
            self.colors = numpy.full((self.num_check ** 2, 3), -1,
                                     dtype=numpy.float)

            if self.check_type in ['board', 'random']:

                # gamma correct high and low
                if MyWindow.gamma_mon is not None:
                    high = MyWindow.gamma_mon(high,
                                              channel=self.contrast_channel)
                    low = MyWindow.gamma_mon(low,
                                             channel=self.contrast_channel)

                self.colors[:, self.contrast_channel] = low

                # index to know how to color elements in array
                self.index = numpy.zeros((self.num_check, self.num_check))

                # populate every other for a checkerboard
                if self.check_type == 'board':
                    self.index[0::2, 0::2] = 1
                    self.index[1::2, 1::2] = 1
                    self.index = numpy.concatenate(self.index[:])

                # randomly populate for a random checkerboard
                elif self.check_type == 'random':
                    self.index = numpy.concatenate(self.index[:])
                    for i in xrange(len(self.index)):
                        self.index[i] = self.fill_random.randint(0, 1)

                # use index to assign colors for board and random
                self.colors[numpy.where(self.index),
                            self.contrast_channel] = high

            elif self.check_type in ['noise', 'noisy noise']:
                numpy.random.seed(self.fill_seed)
                self.colors[:, self.contrast_channel] = numpy.random.uniform(
                    low=low, high=high, size=self.num_check**2)

                # gamma correct
                if MyWindow.gamma_mon is not None:
                    self.colors = MyWindow.gamma_mon(self.colors)

            self.stim = visual.ElementArrayStim(MyWindow.win,
                                                xys=xys,
                                                colors=self.colors,
                                                nElements=self.num_check**2,
                                                elementMask=None,
                                                elementTex=None,
                                                sizes=(self.check_size[0],
                                                       self.check_size[1]),
                                                autoLog=False)

            self.stim.size = (self.check_size[0] * self.num_check,
                              self.check_size[1] * self.num_check)

            if MyWindow.small_win is not None:

                self.small_stim = visual.ElementArrayStim(MyWindow.small_win,
                                                          xys=xys,
                                                          colors=self.colors,
                                                          nElements=self.num_check**2,
                                                          elementMask=None,
                                                          elementTex=None,
                                                          sizes=(self.check_size[0],
                                                                 self.check_size[1]),
                                                          autoLog=False)

                self.small_stim.size = (self.check_size[0] * self.num_check,
                                        self.check_size[1] * self.num_check)

        def gen_timing(self, frame):
            """ElementArrayStim does not support assigning alpha values.

            :param frame: current frame number
            """
            if self.check_type == 'noisy noise':
                self.colors[:, self.contrast_channel] = numpy.random.uniform(
                    low=self.low, high=self.high, size=self.num_check**2)

                # gamma correct
                if MyWindow.gamma_mon is not None:
                    self.colors = MyWindow.gamma_mon(self.colors)

                self.stim.setColors(self.colors)

        def gen_phase(self):
            """ElementArrayStim does not support texture phase.
            """
            pass

        def set_rgb(self, colors):
            """Colors setter.

            :param colors: array of rgb values for each element
            """
            self.stim.setColors(colors)
            if self.small_stim is not None:
                self.small_stim.setColors(colors)

        def set_pos(self, x, y):
            """Position setter. Moves entire array of elements

            :param x: x coordinate
            :param y: y coordinate
            """
            self.stim.setFieldPos((x, y))
            if self.small_stim is not None:
                self.small_stim.setFieldPos((x, y))

        def get_pos(self):
            """Position getter.
            """
            return self.stim.fieldPos

    return BoardTexture()


def movie_stim_class(bases, **kwargs):

    class MovieStim(bases):
        """Movie stims require a unique animate() method, but are otherwise
        similar to other stims.
        """
        def __init__(self):
            """Passes parameters up to super class.
            """
            # pass parameters up to super
            super(MovieStim, self).__init__(**kwargs)

        def make_stim(self):
            """Creates instance of psychopy stim object.
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
            flip() on the window.

            :param frame: current frame number
            """
            # check if within animation range
            if self.end_stim == (frame + 1):
                self.stim.pause()

            super(MovieStim, self).animate(frame)

    return MovieStim()


def log_stats(count_reps, reps, count_frames, num_frames, elapsed_time,
              stim_list, to_animate, time_at_run):
    """Function to write information about stims to file.

    :param count_reps: Elapsed reps.
    :param reps: Total possible reps.
    :param count_frames: Elapsed frames.
    :param num_frames: Total possible frames.
    :param elapsed_time: Elapsed time
    :param stim_list: List of stims that ran.
    :param to_animate: List of stims animated (includes annuli)
    :param time_at_run: Time at which stims were run
    """
    current_time = time_at_run
    current_time_string = strftime('%Y_%m_%d_%H%M%S', current_time)

    if sys.platform == 'win32':
        # log folder
        path = config.get('StimProgram', 'logs_dir')
        if not os.path.exists(path):
            os.makedirs(path)
        # day folder
        path += strftime('%Y_%m_%d', current_time) + '\\'
        if not os.path.exists(path):
            os.makedirs(path)
        # time folder
        path += strftime('%Hh%Mm%Ss', current_time) + '\\'
        if not os.path.exists(path):
            os.makedirs(path)

    elif sys.platform == 'darwin':
        # log folder
        path = config.get('StimProgram', 'logs_dir')
        if not os.path.exists(path):
            os.makedirs(path)
        # day folder
        path += strftime('%Y_%m_%d', current_time) + '/'
        if not os.path.exists(path):
            os.makedirs(path)
        # time folder
        path += strftime('%Hh%Mm%Ss', current_time) + '/'
        if not os.path.exists(path):
            os.makedirs(path)

    # filename format: stimlog_[time]_[stimtype].txt
    file_name = 'stimlog_' + current_time_string + '_' + stim_list[
        0].stim_type.lower() + '.txt'

    with open((path + file_name), 'w') as f:
        f.write(strftime('%a, %d %b %Y %H:%M:%S', current_time))

        f.write("\n{} rep(s) of {} stim(s) generated. ".
                format(reps, len(stim_list)))

        f.write("\n{}/{} frames displayed. ".
                format(count_reps * num_frames + count_frames, reps *
                       num_frames))

        average_fps = (count_reps * num_frames + count_frames) / elapsed_time
        f.write("Average fps: {0:.2f} hz.".format(average_fps))

        f.write("\nElapsed time: {0:.3f} seconds.\n".format(elapsed_time))

        for i in stim_list:
            f.write(str(i))
            f.write('\n')

        f.write('\n\n\n#BEGIN PICKLE#\n')

    with open((path + file_name), 'ab') as f:
        # Pickle dump to be able to load parameters from log file of stim,
        # opened as binary, hence opening twice
        to_write = []
        for i in stim_list:
            para_copy = copy.deepcopy(i.parameters)
            para_copy['move_type'] = i.stim_type
            to_write.append(para_copy)

        f.write(cPickle.dumps(to_write))

    for i in range(len(stim_list)):
        if stim_list[i].parameters['shape'] != 'annulus':

            if stim_list[i].stim_type == 'RandomlyMovingStim':
                file_name = 'Randomlog_' + current_time_string + '.txt'

            if stim_list[i].stim_type == 'MovingStim':
                file_name = 'Movinglog_' + current_time_string + '.txt'

            if stim_list[i].stim_type == 'ImageJumpStim':
                file_name = 'Jumpinglog_' + current_time_string + '.txt'

            if stim_list[i].stim_type in ['RandomlyMovingStim', 'MovingStim']:

                with open((path + file_name), 'w') as f:

                    if has_tabulate:
                        # nicer formatting
                        temp = []
                        for j in range(len(to_animate[i].log[0])):
                            temp.append([to_animate[i].log[0][j],
                                         to_animate[i].log[1][j],
                                         scipy.around(to_animate[i].
                                                      log[2][j][0], 2),
                                         scipy.around(to_animate[i].
                                                      log[2][j][1], 2)])

                        f.write(tabulate(temp,
                                         headers=['angle',
                                                  'frame',
                                                  'pos x',
                                                  'pos y'],
                                         tablefmt="orgtbl"))

                    # ugly formatting
                    else:
                        for j in range(len(to_animate[i].log[0])):
                            f.write('angle: ')
                            f.write(str(to_animate[i].log[0][j]))
                            f.write(' frame: ')
                            f.write(str(to_animate[i].log[1][j]))
                            f.write(' position: ')
                            f.write(str(to_animate[i].log[2][j][0]))
                            f.write(', ')
                            f.write(str(to_animate[i].log[2][j][1]))
                            f.write('\n')

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

            if stim_list[i].stim_type in ['ImageJumpStim']:

                cap = float_uint8(to_animate[i].orig_tex)
                save_name = path + file_name[:-3] + 'npy'
                numpy.save(save_name, numpy.flipud(cap))
                print cap.shape, cap.dtype

                with open((path + file_name), 'w') as f:

                    if has_tabulate:
                        # nicer formatting
                        f.write('image: ' + to_animate[i].image_filename)
                        f.write('\nshuffle: ' + str(to_animate[i].shuffle))
                        f.write('\nimage_channel: ' +
                                str(to_animate[i].image_channel))
                        f.write('\nimage_size: ' +
                                str(to_animate[i].image_size))
                        f.write('\nnum_jumps: ' + str(to_animate[i].num_jumps))
                        f.write('\nmove_seed: ' + str(to_animate[i].move_seed))

                        f.write('\nwindow_size: ' + str(GlobalDefaults[
                                                        'display_size']))
                        f.write('\noffset: ' + str(GlobalDefaults[
                                                   'offset']))
                        f.write('\ntrigger_wait: ' + str(GlobalDefaults[
                                                         'trigger_wait']))
                        f.write('\ngamma_correction: ' + str(GlobalDefaults[
                            'gamma_correction']))
                        f.write('\n\n')

                        f.write(tabulate(to_animate[i].slice_log,
                                         headers=['y_low', 'y_high', 'x_low',
                                                  'x_high'],
                                         tablefmt="orgtbl"))

                    else:
                        raise ImportError('Could not log Jumpstim without '
                                          'tabulate (needs to be implemented).'
                                          )

    return current_time_string


def main(stim_list, verbose=True):
    """Function to create stims and run program. Creates instances of stim
    types, and makes necessary calls to animate stims and flip window.

    :param stim_list: list of StimInfo classes.
    :param verbose: whether or not to print stim info to console.
    :return fps, count_elapsed_time, time_stamp: return stats about last run.
     If error was raised, fps is the error string, and count_elapsed_time is
     'error'.
    """
    current_time = localtime()

    reps = GlobalDefaults['protocol_reps']

    # print stim info if requested
    # if verbose:
    #    for stim in stim_list:
    #        print stim

    # counters for stat tracking
    count_reps = 0
    count_frames = 0
    count_elapsed_time = 0

    # to exit out of nested loops
    MyWindow.should_break = False

    # outer loop for number of reps
    try:
        for x in range(reps):
            # prep stims
            to_animate = []

            for stim in stim_list:
                # print stim.number
                # checkerboard and movie inheritance depends on motion type,
                # so instantiate accordingly
                if stim.parameters['fill_mode'] == 'checkerboard':
                    to_animate.append(board_texture_class(globals()[
                        stim.stim_type], **stim.parameters))

                elif stim.parameters['fill_mode'] == 'movie':
                    to_animate.append(movie_stim_class(globals()
                                      [stim.stim_type], **stim.parameters))

                # all other stims, instantiate by looking up class in
                # globals(), and passing dictionary of parameters
                else:
                    to_animate.append(globals()[
                        stim.stim_type](**stim.parameters))

            # generate stims
            for stim in to_animate:
                stim.make_stim()

            # reset frame trigger times
            del MyWindow.frame_trigger_list[:-1]

            # gen draw times and get end time of last stim
            num_frames = max(stim.draw_times() for stim in to_animate)

            # draw stims and flip window
            if GlobalDefaults['trigger_wait'] != 0:
                MyWindow.win.callOnFlip(MyWindow.send_trigger)
                # print 'trigger'
            MyWindow.flip()

            if GlobalDefaults['trigger_wait'] != 0:
                for y in xrange(GlobalDefaults['trigger_wait'] - 1):
                    MyWindow.flip()

            index = 0
            # clock for timing
            elapsed_time = core.MonotonicClock()

            if GlobalDefaults['capture']:
                capture_dir = os.path.abspath('./psychopy/captures/')
                if not os.path.exists(capture_dir):
                    os.makedirs(capture_dir)
                current_time_string = strftime('%Y_%m_%d_%H%M%S', current_time)
                save_dir = 'capture_' + current_time_string + '_' + stim_list[
                    0].stim_type.lower()
                save_loc = os.path.join(capture_dir, save_dir)
                os.makedirs(save_loc)

            # MyWindow.win.recordFrameIntervals = True

            # for frame in xrange(num_frames):
            # trange for pretty, low overhead (on the order of ns), progress
            # bar in stdout
            for frame in trange(num_frames):
                for stim in to_animate:
                    stim.animate(frame)

                if not GlobalDefaults['capture']:
                    MyWindow.flip()

                # save as movie?
                elif GlobalDefaults['capture']:
                    filename = os.path.join(save_loc,
                                            'capture_' +
                                            str(frame + 1).zfill(5) + '.png')
                    img = MyWindow.win._getRegionOfFrame(buffer='back')
                    img.save(filename, 'PNG')
                    sys.stdout.write('\r')
                    sys.stdout.write(str(int(frame / float(num_frames) * 100) +
                                         1) + '%')
                    sys.stdout.flush()
                    MyWindow.win.clearBuffer()

                if frame == MyWindow.frame_trigger_list[index]:
                    MyWindow.send_trigger()
                    # print frame, 'triggered'
                    index += 1

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

            # MyWindow.win.recordFrameIntervals = False
            # MyWindow.win.saveFrameIntervals()

            # stop movies from continuing in background
            for stim in to_animate:
                if stim.fill_mode == 'movie':
                    stim.stim.pause()

            # outer break
            if MyWindow.should_break:
                print '\n Interrupt!'
                break

            count_reps += 1
    except Exception as e:
        traceback.print_exc()
        return str(e), 'error', None

    # one last flip to clear window if still open
    try:
        MyWindow.flip()
    except AttributeError:
        pass

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
            format(count_reps * (num_frames) + count_frames, reps *
                   (num_frames)),
        print "Average fps: {0:.2f} hz.". \
            format((count_reps * (num_frames) + count_frames) /
                   count_elapsed_time)
        print "Elapsed time: {0:.3f} seconds.\n". \
            format(count_elapsed_time)

    time_stamp = None

    if GlobalDefaults['log']:
        time_stamp = log_stats(count_reps, reps, count_frames, num_frames,
                               count_elapsed_time, stim_list, to_animate,
                               current_time)

    fps = (count_reps * num_frames + count_frames) / count_elapsed_time

    # save movie
    if GlobalDefaults['capture']:
        current_time_string = strftime('%Y_%m_%d_%H%M%S', current_time)
        save_name = 'capture_video' + current_time_string + '.mpg'
        save_name_gray = 'capture_video' + current_time_string + '_gray.mpg'

        args = ['ffmpeg',
                '-f', 'image2',
                '-framerate', str(GlobalDefaults['frame_rate']),
                '-i', os.path.join(save_loc, 'capture_%05d.png'),
                '-b:v', '20M',
                os.path.join(save_loc, save_name)]

        # make movie using ffmpeg
        print 'ffmpeg...'
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        args2 = ['ffmpeg',
                 '-i', os.path.join(save_loc, save_name),
                 '-vf', 'format=gray',
                 '-qscale', '0',
                 os.path.join(save_loc, save_name_gray)]

        print '\ngrayscale conversion...'

        process = subprocess.Popen(args2,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        # print stdout, stderr

        # delete .pngs
        # to_delete = [f for f in os.listdir(save_loc) if f.endswith('.png')]
        # for f in to_delete:
        #     os.remove(os.path.join(save_loc, f))

        print '\nDONE'

    return fps, count_elapsed_time, time_stamp

if __name__ == '__main__':
    pass
