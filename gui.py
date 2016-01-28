#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Program for GUI interface to StimProgram.py"
"""

# must turn pyglet shadow windows off to avoid conflict with wxPython and
# psychopy.visual
import pyglet
pyglet.options['shadow_window'] = False
from collections import OrderedDict
from sys import platform as _platform
from GammaCorrection import GammaValues  # necessary for unpickling
import wx
import StimProgram
import copy
import cPickle
import ConfigParser
from os import system
import os

__author__ = "Alexander Tomlinson"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "tomlinsa@ohsu.edu"
__status__ = "Prototype"


def get_config_dict(config_file):
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    default_config_dict = {}

    options = config.options('Defaults')

    # make dict of options
    for option in options:
        default_config_dict[option] = config.get('Defaults', option)

    # add GUI specific settings
    default_config_dict['savedStimDir'] = config.get('GUI', 'savedStimDir')
    default_config_dict['windowPos'] = config.get('GUI', 'windowPos')

    # stab at casting non-strings
    for key, value in default_config_dict.iteritems():
        # first look for lists
        if default_config_dict[key][0] == '[':
            try:
                # map to int
                default_config_dict[key] = map(int, default_config_dict[
                    key].strip('[]').split(','))
            except ValueError:
                try:
                    # map to float if int mapping fails
                    default_config_dict[key] = map(float, default_config_dict[
                        key].strip('[]').split(','))
                except ValueError:
                    pass
        # # look for booleans
        # elif default_config_dict[key] == 'True':
        #     default_config_dict[key] = True
        # elif default_config_dict[key] == 'False':
        #     default_config_dict[key] = False
        # # look for 'None'
        # elif default_config_dict[key] == 'None':
        #     default_config_dict[key] = None
        # cast non lists
        else:
            try:
                default_config_dict[key] = int(value)
            except ValueError:
                try:
                    default_config_dict[key] = float(value)
                except ValueError:
                    pass

    return default_config_dict

config_file = './psychopy/config.ini'
config_dict = get_config_dict(config_file)

gamma_file = './psychopy/gammaTables.txt'
if os.path.exists(gamma_file):
    with open(gamma_file, 'rb') as f:
        gamma_dict = cPickle.load(f)
    gamma_mons = gamma_dict.keys()
else:
    gamma_mons = []

shape_param = OrderedDict([
    ('shape',
     {'type'    : 'choice',
      'label'   : 'shape',
      'choices' : ['circle', 'rectangle', 'annulus'],
      'default' : config_dict['shape'],
      'is_child': False,
      'children': {
          'circle'   : ['outer_diameter'],
          'rectangle': ['size'],
          'annulus'  : ['inner_diameter', 'outer_diameter']
      }}
     ),

    ('orientation',
     {'type'    : 'text',
      'label'   : 'orientation',
      'default' : config_dict['orientation'],
      'is_child': False}
     ),

    ('location',
     {'type'    : 'list',
      'label'   : 'location (um)',
      'default' : config_dict['location'],
      'is_child': False}
     ),

    ('size',
     {'type'    : 'list',
      'label'   : 'size (um)',
      'default' : config_dict['size'],
      'is_child': True}
     ),

    ('inner_diameter',
     {'type'    : 'text',
      'label'   : 'inner diameter (um)',
      'default' : config_dict['inner_diameter'],
      'is_child': True}
     ),

    ('outer_diameter',
     {'type'    : 'text',
      'label'   : 'outer diameter (um)',
      'default' : config_dict['outer_diameter'],
      'is_child': True}
     ),
])

timing_param = OrderedDict([
    # ('cycle_duration',
    #  {'type'    : 'text',
    #   'label'   : 'cycle duration',
    #   'default' : 1,
    #   'is_child': False}
    #  ),

    ('delay',
     {'type'    : 'text',
      'label'   : 'delay',
      'default' : config_dict['delay'],
      'is_child': False}
     ),

    ('duration',
     {'type'    : 'text',
      'label'   : 'duration',
      'default' : config_dict['duration'],
      'is_child': False}
     ),

    ('trigger',
     {'type'    : 'choice',
      'label'   : 'trigger',
      'choices' : ['True', 'False'],
      'default' : config_dict['trigger'],
      'is_child': False}
     ),

    # ('stim_reps',
    #  {'type'    : 'text',
    #   'label'   : 'stim repetitions',
    #   'default' : 1,
    #   'is_child': False}
    #  ),
])

fill_param = OrderedDict([
    ('color_mode',
     {'type'    : 'choice',
      'label'   : 'color mode',
      'choices' : ['intensity', 'rgb'],
      'default' : config_dict['color_mode'],
      'is_child': False,
      'children': {
          'rgb'        : ['color'],
          'intensity'  : ['intensity', 'contrast_channel'],
      }}
     ),

    ('color',
     {'type'    : 'list',
      'label'   : 'color (RGB)',
      'default' : config_dict['color'],
      'is_child': True}
     ),

    ('contrast_channel',
     {'type'    : 'choice',
      'label'   : 'channel',
      'choices' : ['green', 'red', 'blue', 'global'],
      'default' : config_dict['contrast_channel'],
      'is_child': True}
     ),

    ('intensity',
     {'type'    : 'text',
      'label'   : 'contrast',
      'default' : config_dict['intensity'],
      'is_child': True}
     ),

    ('timing',
     {'type'    : 'choice',
      'label'   : 'timing',
      'choices' : ['step', 'sine', 'square', 'sawtooth', 'linear'],
      'default' : config_dict['timing'],
      'is_child': False,
      'children': {
          'sine'    : ['period_mod'],
          'square'  : ['period_mod'],
          'sawtooth': ['period_mod'],
      }}
     ),

    ('fill_mode',
     {'type'    : 'choice',
      'label'   : 'fill mode',
      'choices' : ['uniform', 'sine', 'square', 'concentric', 'checkerboard',
                   'random', 'image', 'movie'],
      'default' : config_dict['fill_mode'],
      'is_child': False,
      'children': {
          'sine'        : ['sf', 'phase'],
          'square'      : ['sf', 'phase'],
          'concentric'  : ['sf', 'phase'],
          'checkerboard': ['check_size', 'num_check', 'phase'],
          'random'      : ['check_size', 'num_check', 'fill_seed', 'phase'],
          'movie'       : ['movie_filename', 'movie_size'],
          'image'       : ['image_filename', 'image_size'],
      }}
     ),

    ('sf',
     {'type'    : 'text',
      'label'   : 'spatial frequency',
      'default' : config_dict['sf'],
      'is_child': True}
     ),

    ('phase',
     {'type'    : 'list',
      'label'   : 'phase',
      'default' : config_dict['phase'],
      'is_child': True}
     ),

    ('fill_seed',
     {'type'    : 'text',
      'label'   : 'fill seed',
      'default' : config_dict['fill_seed'],
      'is_child': True}
     ),

    ('check_size',
     {'type'    : 'list',
      'label'   : 'check size (xy um)',
      'default' : config_dict['check_size'],
      'is_child': True}
     ),

    ('num_check',
     {'type'    : 'text',
      'label'   : 'number of checks',
      'default' : config_dict['num_check'],
      'is_child': True}
     ),

    ('image_filename',
     {'type'    : 'path',
      'label'   : 'filename',
      'default' : config_dict['image_filename'],
      'is_child': True}
     ),

    ('image_size',
     {'type'    : 'list',
      'label'   : 'size (xy um)',
      'default' : config_dict['image_size'],
      'is_child': True}
     ),

    ('movie_filename',
     {'type'    : 'path',
      'label'   : 'filename',
      'default' : config_dict['movie_filename'],
      'is_child': True}
     ),

    ('movie_size',
     {'type'    : 'list',
      'label'   : 'movie size (xy)',
      'default' : config_dict['movie_size'],
      'is_child': True}
     ),

    ('period_mod',
     {'type'    : 'text',
      'label'   : 'period mod',
      'default' : config_dict['period_mod'],
      'is_child': True}
     ),
])

motion_param = OrderedDict([
    ('move_type',
     {'type'    : 'choice',
      'label'   : 'move type',
      'choices' : ['static', 'moving', 'table', 'random', 'jump'],
      'default' : config_dict['move_type'],
      'is_child': False,
      'children': {
          'moving': ['speed', 'start_dir', 'num_dirs', 'start_radius', 'move_delay'],
          'random': ['speed', 'travel_distance', 'move_seed'],
          'table' : ['table_filename', 'start_dir'],
          'jump'  : ['num_jumps', 'jump_delay', 'move_seed'],
      }}
     ),

    ('speed',
     {'type'    : 'text',
      'label'   : 'speed (um/s)',
      'default' : config_dict['speed'],
      'is_child': True}
     ),

    ('start_dir',
     {'type'    : 'text',
      'label'   : 'start direction',
      'default' : config_dict['start_dir'],
      'is_child': True}
     ),

    ('num_dirs',
     {'type'    : 'text',
      'label'   : 'number of dirs',
      'default' : config_dict['num_dirs'],
      'is_child': True}
     ),

    ('start_radius',
     {'type'    : 'text',
      'label'   : 'start radius (um)',
      'default' : config_dict['start_radius'],
      'is_child': True}
     ),

    ('move_delay',
     {'type'    : 'text',
      'label'   : 'move delay (s)',
      'default' : config_dict['move_delay'],
      'is_child': True}
     ),

    ('travel_distance',
     {'type'    : 'text',
      'label'   : 'travel distance (um)',
      'default' : config_dict['travel_distance'],
      'is_child': True}
     ),

    ('move_seed',
     {'type'    : 'text',
      'label'   : 'move seed',
      'default' : config_dict['move_seed'],
      'is_child': True}
     ),

    ('table_filename',
     {'type'    : 'path',
      'label'   : 'filename',
      'default' : config_dict['table_filename'],
      'is_child': True}
     ),

    ('num_jumps',
     {'type'    : 'text',
      'label'   : 'number of jumps',
      'default' : config_dict['num_jumps'],
      'is_child': True}
     ),

    ('jump_delay',
     {'type'    : 'text',
      'label'   : 'jump delay (frames)',
      'default' : config_dict['jump_delay'],
      'is_child': True}
     )
])

global_default_param = OrderedDict([
    ('display_size',
     {'type'    : 'list',
      'label'   : 'display size (pixels)',
      'default' : config_dict['display_size'],
      'is_child': False}
     ),

    ('position',
     {'type'    : 'list',
      'label'   : 'win position (xy)',
      'default' : config_dict['position'],
      'is_child': False}
     ),

    ('offset',
     {'type'    : 'list',
      'label'   : 'offset (pix)',
      'default' : config_dict['offset'],
      'is_child': False}
     ),

    ('scale',
     {'type'    : 'list',
      'label'   : 'scale (xy)',
      'default' : config_dict['scale'],
      'is_child': False}
     ),

    ('pix_per_micron',
     {'type'    : 'text',
      'label'   : 'pix per micron',
      'default' : config_dict['pix_per_micron'],
      'is_child': False}
     ),

    ('frame_rate',
     {'type'    : 'text',
      'label'   : 'frame rate',
      'default' : config_dict['frame_rate'],
      'is_child': False}
     ),

    ('protocol_reps',
     {'type'    : 'text',
      'label'   : 'protocol reps',
      'default' : config_dict['protocol_reps'],
      'is_child': False}
     ),

    ('trigger_wait',
     {'type'    : 'text',
      'label'   : 'trigger wait',
      'default' : config_dict['trigger_wait'],
      'is_child': False}
     ),

    ('background',
     {'type'    : 'list',
      'label'   : 'background (RGB)',
      'default' : config_dict['background'],
      'is_child': False}
     ),

    ('screen_num',
     {'type'    : 'choice',
      'label'   : 'screen number',
      'choices' : ['1', '2'],
      'default' : str(config_dict['screen_num']),  # to select default,
      # need to be strings
      'is_child': False}
     ),

    ('gamma_correction',
     {'type'    : 'choice',
      'label'   : 'gamma monitor',
      'choices' : ['default'] + gamma_mons,
      'default' : str(config_dict['gamma_correction']),  # to select default,
      # need to be strings
      'is_child': False}
     ),

    ('fullscreen',
     {'type'    : 'choice',
      'label'   : 'fullscreen',
      'choices' : ['True', 'False'],
      'default' : config_dict['fullscreen'],
      'is_child': False}
     ),

    ('log',
     {'type'    : 'choice',
      'label'   : 'log',
      'choices' : ['True', 'False'],
      'default' : config_dict['log'],
      'is_child': False}
     )
    # ('object_list', 1)
])


class TextCtrlTag(wx.TextCtrl):
    """
    Simple subclass of wx.TextCtrl for assigning ID tag to class to keep
    track when passed back in list.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag and tag2 if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        # tag2 used in list type parameters
        self.tag2 = kwargs.pop('tag2', None)
        wx.TextCtrl.__init__(self, *args, **kwargs)


class ChoiceTag(wx.Choice):
    """
    Simple subclass of wx.Choice for assigning ID tag to class to keep
    track when passed back in list.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        wx.Choice.__init__(self, *args, **kwargs)


class FilePickerCtrlTag(wx.FilePickerCtrl):
    """
    Simple subclass of wx.GenericDirCtrl for assigning ID tag to class to keep
    track when passed back in list.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        wx.FilePickerCtrl.__init__(self, *args, **kwargs)


class RadioBoxTag(wx.RadioBox):
    """
    Simple subclass of wx.GenericDirCtrl for assigning ID tag to class to keep
    track when passed back in list.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        wx.RadioBox.__init__(self, *args, **kwargs)


class DirPanel(wx.Panel):
    """
    Class for file browser panel.
    """
    def __init__(self, parent):
        """
        Constructor
        """
        # super instantiation
        super(DirPanel, self).__init__(parent)

        # instance attributes
        self.load_path = None

        # sizer
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # file browser
        if _platform == "darwin":
            self.browser = wx.FileCtrl(self, wildCard='*.txt', size=(200, -1),
                defaultDirectory=config_dict['savedStimDir'])
        elif _platform == "win32":
            self.browser = wx.FileCtrl(self, wildCard='*.txt', size=(200, -1),
                defaultDirectory=config_dict['savedStimDir'])

        # add to sizer
        panel_sizer.Add(self.browser, 1, wx.BOTTOM | wx.TOP | wx.EXPAND,
                        border=5)

        # load and save buttons sizer
        dir_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(self, id=wx.ID_SAVE)
        dir_buttons_sizer.Add(self.save_button, 1, border=5,
                              flag=wx.LEFT | wx.RIGHT)

        self.load_button = wx.Button(self, label="Load")
        dir_buttons_sizer.Add(self.load_button, 1, border=5,
                              flag=wx.LEFT | wx.RIGHT)

        panel_sizer.Add(dir_buttons_sizer, border=5,
                        flag=wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL |
                        wx.ALIGN_CENTER_VERTICAL)

        # load and save button binders
        self.Bind(wx.EVT_BUTTON, self.on_save_button, self.save_button)
        self.Bind(wx.EVT_BUTTON, self.on_load_button, self.load_button)
        self.Bind(wx.EVT_FILECTRL_FILEACTIVATED, self.on_double_click,
                  self.browser)

        self.SetSizer(panel_sizer)

    def on_save_button(self, event):
        """
        Saves current param settings to text file.
        :param event: event passed by binder
        """
        my_frame = event.GetEventObject().GetParent().GetParent()

        if _platform == 'darwin':
            default_dir = './psychopy/stims/'
        elif _platform == 'win32':
            default_dir = '.\\psychopy\\stims\\'

        save_dialog = wx.FileDialog(my_frame, message='File path',
            defaultDir=default_dir,
            wildcard='*.txt', style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if save_dialog.ShowModal() == wx.ID_CANCEL:
            return

        to_save = []
        for stim in my_frame.l1.stim_info_list:
            params = copy.deepcopy(stim.parameters)
            params['move_type'] = stim.stim_type
            to_save.append(params)

        # get path and open file to write
        path = save_dialog.GetPath()

        with open(path, 'wb') as f:
            cPickle.dump(to_save, f)

        # refresh display
        self.browser.ShowHidden(True)
        self.browser.ShowHidden(False)

        print '\nPARAM SAVED'

    def on_load_button(self, event):
        """
        Loads params from parameter file
        :param event: event passed by binder
        """
        my_frame = event.GetEventObject().GetParent().GetParent()

        # get path of settings file from browser
        path = self.browser.GetPath()

        # open and read settings
        if _platform == 'win32':
            is_log = os.path.dirname(path).split('\\')[-2] != 'logs'
            
        if _platform == 'darwin':
            is_log = os.path.dirname(path).split('/')[-2] != 'logs'
            
        
        if is_log:
            with open(path, 'rb') as f:
                to_load = cPickle.load(f)
        else:
            # search file for PICKLE at end
            try:
                with open(path, 'rb') as f:
                    next_is_pickle = False
                    to_load = ""

                    for line in f:
                        if next_is_pickle:
                            to_load += line

                        line = line.rstrip()
                        if line == '#BEGIN PICKLE#':
                            next_is_pickle = True

                    to_load = cPickle.loads(to_load)

            except (ValueError):
                print "\nERROR: file not a properly formatted parameter file"
                return

        # load list
        for stim_param in to_load:
            stim_type = stim_param.pop('move_type')

            if stim_type == 'StaticStim':
                stim_type = 'static'
            elif stim_type == 'MovingStim':
                stim_type = 'moving'
            elif stim_type == 'RandomlyMovingStim':
                stim_type = 'random'
            elif stim_type == 'TableStim':
                stim_type = 'table'
            elif stim_type == 'ImageJumpStim':
                stim_type = 'jump'

            my_frame.l1.add_stim(stim_type, stim_param)

        print '\nSTIMS LOADED'

    def on_double_click(self, event):
        """
        opens file for user to inspect if log file, else loads
        :param event:
        :return:
        """
        my_frame = event.GetEventObject().GetParent().GetParent()

        # get path of settings file from browser
        path = self.browser.GetPath()

        # open and read settings
        if _platform == 'win32':
            if os.path.dirname(path).split('\\')[-2] == 'logs':
                os.startfile(path)
            else:
                self.on_load_button(event)

        elif _platform == 'darwin':
            if os.path.dirname(path).split('/')[-2] == 'logs':
                os.system('open ' + path)
            else:
                self.on_load_button(event)


class ListPanel(wx.Panel):
    """
    Class for panel with list of stims to be presented
    """
    def __init__(self, parent):
        """
        Constructor
        """
        # super instantiation
        super(ListPanel, self).__init__(parent)

        # instance attributes
        self.stim_info_list = []
        self.index = 0

        # sizer
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # title
        title = wx.StaticText(self, label="Stims to run")
        panel_sizer.Add(title, flag=wx.TOP, border=10)

        # list control widget
        self.list_control = wx.ListCtrl(self, size=(200, -1),
                                        style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_control.InsertColumn(0, 'Shape')
        self.list_control.InsertColumn(1, 'Type')
        self.list_control.InsertColumn(2, 'Fill')
        self.list_control.InsertColumn(3, 'Trigger')

        # add to sizer
        panel_sizer.Add(self.list_control, 1, wx.BOTTOM | wx.TOP | wx.EXPAND,
                        border=10)

        # add and remove buttons sizer
        list_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_button = wx.Button(self, id=wx.ID_ADD)
        list_buttons_sizer.Add(self.add_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        self.remove_button = wx.Button(self, id=wx.ID_REMOVE)
        list_buttons_sizer.Add(self.remove_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        panel_sizer.Add(list_buttons_sizer, border=5,
                        flag=wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL |
                        wx.ALIGN_CENTER_VERTICAL)

        # load and save button binders
        self.Bind(wx.EVT_BUTTON, self.on_add_button, self.add_button)
        self.Bind(wx.EVT_BUTTON, self.on_remove_button, self.remove_button)
        # self.Bind(wx.EVT_BUTTON, self.on_clear_button, self.clear_button)
        # double click to load binder
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_double_click,
                  self.list_control)

        self.SetSizer(panel_sizer)

    def on_add_button(self, event):
        """
        Gets stim params from event, to pass to add_stim.
        :param event: event passed by binder
        """
        my_frame = event.GetEventObject().GetParent().GetParent()

        # add to stim list control
        stim_type = my_frame.panel_move.param_dict['move_type'][
            'default']

        # merge
        param_dict = copy.deepcopy(my_frame.merge_dicts())

        self.add_stim(stim_type, param_dict)

    def add_stim(self, stim_type, param_dict):
        """
        Adds stim to list of stims to run
        :param stim_type:
        :param param_dict:
        :return:
        """
        shape = param_dict['shape']
        fill = param_dict['fill_mode']
        trigger = str(param_dict['trigger'])

        # add info to list
        self.list_control.InsertStringItem(self.index, shape)
        self.list_control.SetStringItem(self.index, 1, stim_type)
        self.list_control.SetStringItem(self.index, 2, fill)
        self.list_control.SetStringItem(self.index, 3, trigger)
        # resize columns to fit
        self.list_control.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(3, wx.LIST_AUTOSIZE)

        if stim_type == 'static':
            stim_type = 'StaticStim'
        elif stim_type == 'moving':
            stim_type = 'MovingStim'
        elif stim_type == 'random':
            stim_type = 'RandomlyMovingStim'
        elif stim_type == 'table':
            stim_type = 'TableStim'
        elif stim_type == 'jump':
            stim_type = 'ImageJumpStim'

        stim_info = StimProgram.StimInfo(stim_type, param_dict,
                                         self.index + 1)
        self.stim_info_list.append(stim_info)

        self.index += 1

    def on_remove_button(self, event):
        """
        Removes stims from stim list. If none selected, clears all
        :param event:
        """
        if self.list_control.GetSelectedItemCount() > 0:
            for i in range(self.list_control.GetSelectedItemCount()):
                selected = self.list_control.GetFirstSelected()
                # print int(selected)
                self.stim_info_list.pop(selected)
                self.list_control.DeleteItem(selected)
                self.index -= 1
        else:
            self.list_control.DeleteAllItems()
            del self.stim_info_list[:]
            self.index = 0

    def on_double_click(self, event):
        """
        Loads params from list on double click
        :param event:
        """
        my_frame = event.GetEventObject().GetParent().GetParent()

        # get param list
        selected = self.list_control.GetFirstSelected()
        param_dict = copy.deepcopy(self.stim_info_list[selected].parameters)

        # change True/False back to string
        for k, v in param_dict.iteritems():
            if type(v) == bool and v == True:
                param_dict[k] = 'True'
            elif type(v) == bool and v == False:
                param_dict[k] = 'False'

        # re-add stim type
        stim_type = copy.deepcopy(self.stim_info_list[selected].stim_type)
        if stim_type == 'StaticStim':
            stim_type = 'static'
        elif stim_type == 'MovingStim':
            stim_type = 'moving'
        elif stim_type == 'RandomlyMovingStim':
            stim_type = 'random'
        elif stim_type == 'TableStim':
            stim_type = 'table'
        elif stim_type == 'ImageJumpStim':
            stim_type = 'jump'

        param_dict['move_type'] = stim_type

        # load in panels and subpanels
        for panel in my_frame.input_nb.GetChildren():
            for param, control in panel.input_dict.iteritems():
                panel.set_value(param, param_dict[param])
            for value in panel.sub_panel_dict.itervalues():
                for subpanel in value.itervalues():
                    for param, control in subpanel.input_dict.iteritems():
                        subpanel.set_value(param, param_dict[param])

        print '\nPARAM LOADED'


class InputPanel(wx.Panel):
    """
    Class for generic panel with input widgets and labels.
    Also superclass of SubPanel and GlobalPanel.
    """
    def __init__(self, params, parent):
        """
        Constructor
        :param params: dictionary of parameters with associated information
        :param parent: parent of window
        """
        # super instantiation
        super(InputPanel, self).__init__(parent)
        self.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

        # instance attributes
        self.sub_panel_dict = None
        self.type = None
        self.input_dict = None
        self.verbose = False

        # load defaults
        self.param_dict = OrderedDict(params)

        # create sizer
        self.grid = wx.GridBagSizer(hgap=5, vgap=5)

        self.i = 0  # list counter
        self.j = 0  # pos in sizer counter

        # method for recursively generating label and input fields
        self.create_inputs()

        # nest and place sizers
        win_sizer = wx.BoxSizer()
        win_sizer.Add(self.grid, 1, wx.ALL | wx.EXPAND, border=10)

        # set sizer
        self.SetSizer(win_sizer)

    def create_inputs(self):
        """
        Method to recursively generate label and input widgets.
        Checks if param is child of another and only generates
        parent params, then generates subpanel with associated child
        params. Differentiates between input types (text, dropdown,
        list (i.e. multiple text fields).
        """
        # trackers for various widgets
        param_list = []
        input_dict = {}
        self.input_dict = input_dict

        # dictionary to store SubPanel information when generated
        self.sub_panel_dict = {}

        # iterates through key/values pairs in param dict
        # k is the parameter (eg. fill_mode)
        # v is the dictionary of associated details (type:circle,
        # is_child:False, etc.)
        for k, v in self.param_dict.iteritems():
            # only generate fields for parent params
            if not v['is_child']:
                # label widget
                param_list.append(
                    wx.StaticText(self, label=str(v['label'] + ':')))

                # various input widgets
                if v['type'] == 'text':
                    input_dict[k] = (TextCtrlTag(self, size=(120, -1), tag=k,
                                                 value=str(v['default']),
                                                 validator=TextCtrlValidator()))
                    # binds event to method (so input_update() method is called
                    # on each wx.EVT_TEXT event.
                    self.Bind(wx.EVT_TEXT, self.input_update,
                              input_dict[k])
                    # input_dict[k].Bind(wx.EVT_SET_FOCUS, self.on_focus)

                elif v['type'] == 'choice':
                    input_dict[k] = (ChoiceTag(self, tag=k,
                                               choices=v['choices']))
                    # on windows, choices still default to blank, so manually
                    # set selection to default for aesthetics
                    input_dict[k].SetStringSelection(v['default'])
                    # same as above, but for wx.EVT_CHOICE event
                    self.Bind(wx.EVT_CHOICE, self.input_update,
                              input_dict[k])

                elif v['type'] == 'path':
                    input_dict[k] = (FilePickerCtrlTag(self, tag=k,
                                     message='Path to file',
                                     style=wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL))
                    self.Bind(wx.EVT_FILEPICKER_CHANGED,
                              self.input_update, input_dict[k])

                elif v['type'] == 'list':
                    # get length of list for sizer and TextCtrl sizing
                    length = len(v['default'])
                    # sizer for adding text boxes into grid
                    list_sizer = wx.GridSizer(rows=1, cols=length, hgap=5)
                    # list of TextCtrl list widgets
                    list_list = []
                    # iterate through number of fields in each list and
                    # create a TextCtrl for each, with tag2 as the position
                    # of the input in the param list
                    # also resize TextCtrl so lengths match up for aesthetic
                    # purposes
                    # TODO: find a better way to size list TextCtrl
                    for i in range(length):
                        list_list.append(TextCtrlTag(self, tag=k, tag2=i,
                        size=((120 / length - (5 * (length - 1)) / length),
                              -1),  # -1 defaults to appropriate size
                              value=str(v['default'][i]),
                              validator=TextCtrlValidator()))
                        # add to sizer
                        list_sizer.Add(list_list[i])
                        # bind
                        self.Bind(wx.EVT_TEXT, self.input_update, list_list[i])
                    # add sizer to input_dict for inclusion in grid
                    input_dict[k] = list_sizer

                elif v['type'] == 'radio':
                    input_dict[k] = (RadioBoxTag(self, tag=k, choices=v[
                                     'choices'], style=wx.RA_SPECIFY_COLS,
                                     majorDimension=2))
                    input_dict[k].SetStringSelection(v['default'])
                    self.Bind(wx.EVT_RADIOBOX, self.input_update,
                              input_dict[k])

                # add widgets to sizer
                self.grid.Add(param_list[self.i], pos=(self.j, 0))
                self.grid.Add(input_dict[k], pos=(self.j, 1))

                # increment counters
                # separate counters because subpanels increase grid count
                # without increasing list count
                self.i += 1  # list
                self.j += 1  # grid

            # checks if param has child params
            if 'children' in v:
                # create a new dictionary in sub panel dict for that parameter
                # necessary because some panels have more than one subpanel,
                # and the proper subpanel needs to be referenced on calls
                # to Show() and Hide()
                self.sub_panel_dict[k] = {}

                # single sizer so that subpanels can occupy the same space
                sub_sizer = wx.BoxSizer(wx.VERTICAL)

                # iterate through the dictionary of child params
                # k2 is value of choice with child params
                # v2 is a list of the associated child params
                for k2, v2 in self.param_dict[k]['children'].iteritems():
                    # instantiate new ordered dict to hold child params to be
                    # generated on subpanel instantiated
                    sub_param_dict = OrderedDict()

                    # iterates through list of child params and creates
                    # copy of dict entry found in param_dict
                    # can't use = otherwise changes to sub_param_dict will
                    # make changes in param_dict
                    for item in self.param_dict[k]['children'][k2]:
                        sub_param_dict[item] = copy.deepcopy(
                            self.param_dict[item])
                    # iterate through new sub_param_dict
                    # k3 is the param name
                    # v3 is the dictionary of associated details
                    for k3, v3 in sub_param_dict.iteritems():
                        # set is_child to False so that on call to
                        # create_inputs() widgets will be created
                        v3['is_child'] = False

                    # instantiate subpanel with new dict
                    self.sub_panel_dict[k][k2] = SubPanel(sub_param_dict, self,
                                                          self.param_dict)

                # add panels to sub sizer
                for k4, v4 in self.sub_panel_dict[k].iteritems():
                    sub_sizer.Add(v4, 1)

                # add sub sizer to grid sizer, spanning both columns
                self.grid.Add(sub_sizer, pos=(self.j, 0), span=(1, 2))
                # increment sizer counter
                self.j += 1

    # def on_focus(self, event):
    #     """
    #     Method to call highlight_all when focused. Required to due needing to
    #     use wx.CallAfter, since on_focus does its own set_selection which
    #     overrides highlight_all's.
    #     :param event: wxPython event, passed by binder
    #     """
    #     textctrl = event.GetEventObject()
    #     wx.CallAfter(self.select_all, textctrl)

    def select_all(self, textctrl):
        """
        Method to highlight all on focus, for easier replacing, especially
        when tabbing on OSX where default behavior is not to highlight.
        """
        textctrl.SelectAll()

    def input_update(self, event):
        """
        Method for updating param_dict on changes to input widgets
        :param event: wxPython event, passed by binder
        """
        self.Validate()
        # Get tag of object (which is param)
        param = event.GetEventObject().tag
        # start printing changes
        if self.verbose:
            print param,

        # get the new value from the widget
        value = event.GetString()

        # attempt to cast to float or int, else leave as is (hopefully string)
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass

        # if a list type param, change the appropriate list item by getting
        # tag2 (list index)
        if self.param_dict[param]['type'] == 'path':
            self.param_dict[param]['default'] = event.GetPath()
        elif self.param_dict[param]['type'] == 'text':
            self.param_dict[param]['default'] = value
        elif self.param_dict[param]['type'] == 'choice':
            self.param_dict[param]['default'] = value
        elif self.param_dict[param]['type'] == 'radio':
            self.param_dict[param]['default'] = \
                event.GetEventObject().GetStringSelection()
        elif self.param_dict[param]['type'] == 'list':
            self.param_dict[param]['default'][event.GetEventObject().tag2] = \
                value

        # finish printing info
        if self.verbose:
            print "set to {}.".format(self.param_dict[param]['default'])

        # hide/show panels if necessary
        if 'children' in self.param_dict[param]:
            # iterate through all the subpanel and show/hide as needed
            for item in self.param_dict[param]['children']:
                if item == value:
                    self.sub_panel_dict[param][item].Show()
                else:
                    self.sub_panel_dict[param][item].Hide()
            # redraw
            self.Fit()

    def get_param_dict(self):
        """
        Method for returning a dictionary with extra info stripped out,
        to eventually pass to StimProgram.py
        """
        params = {}
        for k, v in self.param_dict.iteritems():
            if v['default'] == 'True':
                v['default'] = True
            elif v['default'] == 'False':
                v['default'] = False
            params[k] = v['default']

        # remove move type from dictionary and set as instance attribute
        if 'move_type' in params:
            stim_type = params.pop('move_type')
            if stim_type == 'static':
                self.type = 'StaticStim'
            elif stim_type == 'moving':
                self.type = 'MovingStim'
            elif stim_type == 'random':
                self.type = 'RandomlyMovingStim'
            elif stim_type == 'table':
                self.type = 'TableStim'
            elif stim_type == 'jump':
                self.type = 'ImageJumpStim'

        return params

    def set_value(self, param, value):
        """
        Method to change control values on load. SetValue() simulates user
        input and so generates an event, but SetStringSelection() does not,
        so it is necessary to simulate the choice event.
        :param value:
        :param param:
        """
        # checks which type of control to determine how to set value
        if self.param_dict[param]['type'] == 'text':
            self.input_dict[param].SetValue(str(value))

        elif self.param_dict[param]['type'] == 'path':
            self.input_dict[param].SetPath(str(value))

        elif self.param_dict[param]['type'] == 'radio':
            self.input_dict[param].SetStringSelection(str(value))

        elif self.param_dict[param]['type'] == 'choice':
            # simulate event, for panel switching
            event = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED,
                                    self.input_dict[param].Id)
            event.SetEventObject(self.input_dict[param])
            event.SetInt(1)
            event.SetString(value)
            self.input_dict[param].Command(event)
            global app
            app.ProcessPendingEvents()

            self.input_dict[param].SetStringSelection(str(value))

        elif self.param_dict[param]['type'] == 'list':
            childs = self.input_dict[param].GetChildren()
            for i in range(len(value)):
                widgets = childs[i].GetWindow()
                widgets.SetValue(str(value[i]))


class SubPanel(InputPanel):
    """
    Class for subpanels, in order to override input_update
    """
    def __init__(self, params, parent, parent_params):
        """
        :param params: dictionary of children parameters to be generated
        :param parent: parent window
        :param parent_params: dictionary where parameters of parent param
        are stored, so that those are changed rather than in sub_param_dict
        """
        super(SubPanel, self).__init__(params, parent)
        self.parent_params = parent_params

    def input_update(self, event):
        """
        same as super class input_update, except that changes are made to
        param dict that parent belongs to
        :param event:
        """
        param = event.GetEventObject().tag
        if self.verbose:
            print param,

        value = event.GetString()

        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass

        if self.param_dict[param]['type'] == 'path':
            self.parent_params[param]['default'] = event.GetPath()
        elif self.param_dict[param]['type'] == 'text':
            self.parent_params[param]['default'] = value
        elif self.param_dict[param]['type'] == 'choice':
            self.parent_params[param]['default'] = value
        elif self.param_dict[param]['type'] == 'radio':
            self.parent_params[param]['default'] = event.GetStringSelection()
        elif self.param_dict[param]['type'] == 'list':
            self.parent_params[param]['default'][event.GetEventObject().tag2] \
                = value

        if self.verbose:
            print "set to {}.".format(self.parent_params[param]['default'])


class GlobalPanel(InputPanel):
    """
    Subclass of InputPanel, contains a few aesthetic changes in its init
    since not part of a notebook
    """
    def __init__(self, parent, params):
        # super initiation
        super(GlobalPanel, self).__init__(parent, params)

        # move items down a few slots to insert spacers and titles
        for item in reversed(self.grid.GetChildren()):
            x, y = item.GetPosTuple()
            x += 2
            pos = x, y
            item.SetPos(pos)

        # title
        self.title = wx.StaticText(self, label="Global Defaults")
        self.grid.Add(self.title, pos=(0, 0), span=(1, 2))

        # spacers
        self.grid.Add((5, 5), pos=(1, 0))


class TextCtrlValidator(wx.PyValidator):
    """
    Validator class to ensure proper entry of parameters
    """
    def __init__(self):
        """
        normal constructor
        """
        wx.PyValidator.__init__(self)

    def Clone(self):
        """
        Standard cloner.
        All validators are required to implement the Clone() method.
        """
        return TextCtrlValidator()

    def Validate(self, win):
        """
        Validate contents of given TextCtrl.
        :param win:
        """
        text_box = self.GetWindow()
        value = text_box.GetValue()

        try:
            value = int(value)
            text_box.SetBackgroundColour('white')
            text_box.Refresh()
            return True
        except ValueError:
            try:
                value = float(value)
                text_box.SetBackgroundColour('white')
                text_box.Refresh()
                return True
            except ValueError:
                text_box.SetBackgroundColour('pink')
                text_box.Refresh()
                return False

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True


class MyFrame(wx.Frame):
    """
    Class for generating window. Instantiates notebook and panels.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor. Creates and lays out panels in sizers, finally hiding
        necessary subpanels.
        """
        # super initiation
        super(MyFrame, self).__init__(*args, **kwargs)

        # instance attributes
        self.win_open = False
        self.background = None

        # notebook to hold input panels
        self.input_nb = wx.Notebook(self)

        # instantiate panels with notebook as parent
        self.panel_shape = InputPanel(shape_param, self.input_nb)
        self.panel_timing = InputPanel(timing_param, self.input_nb)
        self.panel_move = InputPanel(motion_param, self.input_nb)
        self.panel_fill = InputPanel(fill_param, self.input_nb)

        # add panels to notebook
        self.input_nb.AddPage(self.panel_shape, "Shape")
        self.input_nb.AddPage(self.panel_timing, "Time")
        self.input_nb.AddPage(self.panel_fill, " Fill ")
        self.input_nb.AddPage(self.panel_move, "Motion")

        # sizer to hold notebook and global panel
        panel_row = wx.BoxSizer(wx.HORIZONTAL)

        # add notebook to sizer
        panel_row.Add(self.input_nb, 1, wx.EXPAND)

        # instantiate global panel and add to sizer
        self.g1 = GlobalPanel(global_default_param, self)
        panel_row.Add(self.g1, 1, wx.TOP | wx.EXPAND, border=5)

        # sizer for buttons under panel_row
        stim_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create buttons and add to button sizer
        self.run_button = wx.Button(self, label="Run")
        stim_buttons_sizer.Add(self.run_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        self.stop_button = wx.Button(self, label="Stop")
        stim_buttons_sizer.Add(self.stop_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        self.win_button = wx.Button(self, label="Window")
        stim_buttons_sizer.Add(self.win_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        self.calib_button = wx.Button(self, label="Calib")
        stim_buttons_sizer.Add(self.calib_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        self.exit_button = wx.Button(self, label="Exit")
        stim_buttons_sizer.Add(self.exit_button, 1, border=5,
                               flag=wx.LEFT | wx.RIGHT)

        # binders
        self.Bind(wx.EVT_BUTTON, self.on_run_button, self.run_button)
        self.Bind(wx.EVT_BUTTON, self.on_win_button, self.win_button)
        self.Bind(wx.EVT_BUTTON, self.on_stop_button, self.stop_button)
        self.Bind(wx.EVT_BUTTON, self.on_calib_button, self.calib_button)
        self.Bind(wx.EVT_BUTTON, self.on_exit_button, self.exit_button)

        # sizer for panel and buttons
        panel_button_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_button_sizer.Add(panel_row, 1, wx.EXPAND)
        panel_button_sizer.Add(stim_buttons_sizer, border=10,
                               flag=wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL |
                               wx.ALIGN_CENTER_VERTICAL)

        # save and list panels
        self.l1 = ListPanel(self)
        self.b1 = DirPanel(self)

        # window sizer, to hold panel_button_sizer and save and list panels
        self.win_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.win_sizer.Add(self.b1, 1, wx.EXPAND | wx.ALL, border=5)
        self.win_sizer.Add(self.l1, 1, wx.EXPAND | wx.TOP | wx.RIGHT |
                           wx.BOTTOM, border=5)
        self.win_sizer.Add(panel_button_sizer)

        # place on monitor (arbitrary, from ini)
        pos = config_dict['windowPos'][0], config_dict['windowPos'][1]
        self.SetPosition(pos)

        # HACK FOR PROPER SIZING
        # TODO: better sizing
        # (hide all subpanels, then show largest, then fit, then hide and show
        # appropriate subpanels)

        # hide all subpanels
        for panel in self.input_nb.GetChildren():
            for k in iter(panel.sub_panel_dict.viewkeys()):
                for k2 in iter(panel.sub_panel_dict[k].viewkeys()):
                    panel.sub_panel_dict[k][k2].Hide()

        # show largest subpanel
        self.panel_fill.sub_panel_dict['fill_mode']['random'].Show()

        # set sizer
        self.SetSizer(self.win_sizer)
        self.win_sizer.Fit(self)

        # show/hide subpanels
        for panel in self.input_nb.GetChildren():
            for k in iter(panel.sub_panel_dict.viewkeys()):
                for k2 in iter(panel.sub_panel_dict[k].viewkeys()):
                    if k2 != panel.param_dict[k]['default']:
                        panel.sub_panel_dict[k][k2].Hide()
                    else:
                        panel.sub_panel_dict[k][k2].Show()
                        panel.Fit()


        # key interrupts
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keypress)

        # draw frame
        self.Show()

    def merge_dicts(self):
        """
        Merges dictionaries with params from each panel
        """
        dicts = {}

        dicts.update(self.panel_shape.get_param_dict())
        dicts.update(self.panel_timing.get_param_dict())
        dicts.update(self.panel_fill.get_param_dict())
        dicts.update(self.panel_move.get_param_dict())

        return dicts

    def on_run_button(self, event):
        """
        Method for running stimulus. Makes call to StimProgram.py. Gets
        necessary params from global panel (g1)
        :param event: event passed by binder
        :return:
        """
        # checks if stim window is open or not, to determine if needs to open a
        # window by making call to on_win_button
        if len(self.l1.stim_info_list) != 0:
            if self.win_open:
                # try/except, so that errors thrown by StimProgram can be
                # caught and thrown to avoid hanging.
                self.on_stop_button(event)
                try:
                    StimProgram.main(self.l1.stim_info_list)
                except:
                    raise
            else:
                self.on_win_button(event)
                self.on_run_button(event)
        else:
            print "Please add stims."

    def on_win_button(self, event):
        """
        Method for regenerating stim window. Makes call to StimProgram. Gets
        size from global panel.
        :param event: event passed by binder
        :return:
        """
        if self.win_open:
            self.on_stop_button(event)
            StimProgram.MyWindow.close_win()
            self.win_open = False
        else:
            defaults = self.g1.get_param_dict()
            # change scale from pix to 0-1
            defaults["offset"] = [float(defaults["offset"][0])/
                                    defaults['display_size'][0]*2,
                                  float(defaults["offset"][1])/
                                    defaults['display_size'][1]*2]
            # if defaults['fullscreen'] == "True":
            #     defaults['fullscreen'] = True
            # else:
            #     defaults['fullscreen'] = False
            defaults['screen_num'] = int(defaults['screen_num']) - 1

            self.win_open = True
            StimProgram.GlobalDefaults(**defaults)
            StimProgram.MyWindow.make_win()

    def on_stop_button(self, event):
        """
        Method for stopping stim. Makes call to StimProgram.
        :param event: event passed by binder
        """
        StimProgram.MyWindow.should_break = True

    def on_calib_button(self, event):
        """
        Method for calling gamma correction script
        :param event: event passed by binder
        :return:
        """
        if _platform == 'win32':
            system('start python GammaCorrection.pyc')

        elif _platform == 'darwin':
            current_dir = os.getcwd()
            system('open -n -a Terminal.app {}'.format(current_dir))


    def on_exit_button(self, event):
        """
        Closes application.
        :param event: event passed by binder
        """
        if self.win_open:
            self.on_stop_button(event)
            StimProgram.MyWindow.close_win()
        self.Close()

    def on_keypress(self, event):
        """
        Interrupt stim if escape key is pressed.

        :param event: event passed by binder
        """
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            print 'escaped'
            self.on_stop_button(event)

        elif event.GetKeyCode() == wx.WXK_DELETE:
            if self.win_open:
                print 'window closed'
                self.on_win_button(event)

        event.Skip()


def main():
    # instantiate app
    global app
    app = wx.App(False)
    # instantiate window
    frame = MyFrame(None)
    # run app
    app.MainLoop()

if __name__ == "__main__":
    main()
