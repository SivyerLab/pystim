#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Test of MVC framework for GUI.
"""

from GammaCorrection import GammaValues  # necessary for pickling
from collections import OrderedDict
from copy import deepcopy
from sys import platform
import ConfigParser
import StimProgram
import wx, wx.grid
import cPickle
import os


class Parameters(object):
    """
    Model to hold parameter data.
    """

    def __init__(self):
        # instance attributes
        self.shape_param = None
        self.timing_param = None
        self.fill_param = None
        self.motion_param = None
        self.global_default_param = None

        self.gui_params = None

        # init params
        config_file = os.path.abspath('.\psychopy\config.ini')
        self.gui_params, config_dict = self.read_config_file(config_file)
        self.init_params(config_dict)

    def read_config_file(self, config_file):
        """
        Uses ConfigParser to read .ini file where default values for params
        are stored.
        :param config_file: file where defaults are stored
        :return: returns dictionary of defaults
        """
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        default_config_dict = {}
        gui_config_dict = {}

        # make dict of options
        for option in config.options('Defaults'):
            default_config_dict[option] = config.get('Defaults', option)

        # make dict of gui options
        for option in config.options('GUI'):
            gui_config_dict[option] = config.get('GUI', option)

        # cast, so that lists are not strings for proper set up of controls
        for key, value in default_config_dict.iteritems():
            default_config_dict[key] = self.try_cast(value)

        for key, value in gui_config_dict.iteritems():
            gui_config_dict[key] = self.try_cast(value)

        return gui_config_dict, default_config_dict

    def try_cast(self, value):
        """
        helper method to attempt to cast parameters from strings to proper
        int/float/bool, or map list values to int or float

        :param value: variable being casted, passed from ini file or gui so
        always string. Skip if string
        :return: casted or unchanged variable
        """
        if isinstance(value, basestring) and value != '':
            # first look for lists
            if value[0] == '[':
                try:
                    # map to int
                    value = map(int, value.strip('[]').split(','))
                except ValueError:
                    try:
                        # map to float if int mapping fails
                        value = map(float, value.strip('[]').split(','))
                    except ValueError:
                        pass
            # cast non lists
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        # check if string is 'None' or bool
                        if value == 'None':
                            value = None
                        elif value == 'True':
                            value = True
                        elif value == 'False':
                            value = False
                        else:
                            pass

        else:
            pass

        return value

    def trans(self, category):
        """
        Helper method to go from category to appropriate dictionary

        :param category: which dictionary the param is in
        :return: dictionary
        """
        trans = {'shape' : self.shape_param,
                 'timing': self.timing_param,
                 'fill'  : self.fill_param,
                 'motion': self.motion_param,
                 'global': self.global_default_param}

        return trans[category]

    def get_gammas(self):
        """
        Getter

        :return: returns list of saved gamma profiles
        """
        gamma_file = os.path.abspath('./psychopy/data/gammaTables.txt')

        if os.path.exists(gamma_file):
            with open(gamma_file, 'rb') as f:
                gamma_dict = cPickle.load(f)
            gamma_mons = gamma_dict.keys()
        else:
            gamma_mons = []

        return gamma_mons

    def get_params(self, category):
        """
        Getter

        :param category: which dictionary the param is in
        """
        trans = self.trans(category)

        return deepcopy(trans)

    def get_global_params(self):
        """"
        Getter.

        :return: dictionary of default values from global defaults
        """
        global_dict = {}

        for param in self.global_default_param.keys():
            global_dict[param] = self.global_default_param[param]['default']

        return global_dict

    def get_gui_params(self):
        """
        Getter

        :return: dictionary of gui settings
        """
        return self.gui_params

    def get_merged_params(self):
        """
        Getter.

        :return: dictionary of default values from dicts other than global
        defaults
        """
        merged_params = {}

        for param_dict in [self.shape_param,
                           self.timing_param,
                           self.fill_param,
                           self.motion_param]:

            for param in param_dict.keys():
                merged_params[param] = param_dict[param]['default']

        return deepcopy(merged_params)

    def set_param_value(self, category, param, value, index=None):
        """
        Setter

        :param category: which dictionary the param is in
        :param param: the param to be edited
        :param value: the value the param is being set to
        :parma index: if a list value param, where in the list
        """
        trans = self.trans(category)

        value = self.try_cast(value)

        if index is None:
            trans[param]['default'] = value
        else:
            trans[param]['default'][index] = value

        # print '{} set to {}.'.format(param, repr(trans[param]['default']))

    def get_param_value(self, category, param, index=None):
        """
        Getter

        :param category: which dictionary the param is in
        :param param: the param to be returned
        :parma index: if a list value param, where in the list
        """
        trans = self.trans(category)

        if index is None:
            return trans[param]['default']
        else:
            return trans[param]['default'][index]

    def init_params(self, config_dict):
        """
        Initializes dictionaries of parameters

        :param config_dict: dictionary of defaults
        """
        self.shape_param = OrderedDict([
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

        self.timing_param = OrderedDict([
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

            ('force_stop',
             {'type'    : 'text',
              'label'   : 'end (non 0 overrides)',
              'default' : config_dict['force_stop'],
              'is_child': False}
             ),

            ('trigger',
             {'type'    : 'choice',
              'label'   : 'trigger',
              'choices' : ['True', 'False'],
              'default' : config_dict['trigger'],
              'is_child': False}
             ),
        ])

        self.fill_param = OrderedDict([
            ('color_mode',
             {'type'    : 'choice',
              'label'   : 'color mode',
              'choices' : ['intensity', 'rgb'],
              'default' : config_dict['color_mode'],
              'is_child': False,
              'children': {
                  'rgb'        : ['color', 'contrast_channel'],
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
              'choices' : ['green', 'red', 'blue'],
              'default' : config_dict['contrast_channel'],
              'is_child': True}
             ),

            ('intensity',
             {'type'    : 'text',
              'label'   : 'intensity',
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
                  'sine'    : ['period_mod', 'intensity_dir'],
                  'square'  : ['period_mod', 'intensity_dir'],
                  'sawtooth': ['period_mod', 'intensity_dir'],
                  'linear'  : ['intensity_dir']
              }}
             ),

            ('fill_mode',
             {'type'    : 'choice',
              'label'   : 'fill mode',
              'choices' : ['uniform', 'sine', 'square', 'concentric',
                           'checkerboard', 'random', 'image', 'movie'],
              'default' : config_dict['fill_mode'],
              'is_child': False,
              'children': {
                  'sine'        : ['intensity_dir', 'sf', 'phase',
                                   'phase_speed'],
                  'square'      : ['intensity_dir', 'sf', 'phase',
                                   'phase_speed'],
                  'concentric'  : ['intensity_dir', 'sf', 'phase',
                                   'phase_speed'],
                  'checkerboard': ['check_size', 'num_check', 'phase',
                                   'intensity_dir'],
                  'random'      : ['check_size', 'num_check', 'fill_seed',
                                   'phase', 'intensity_dir'],
                  'movie'       : ['movie_filename', 'movie_size'],
                  'image'       : ['image_filename', 'image_size', 'phase',
                                   'phase_speed', 'image_channel'],
              }}
             ),

            ('alpha',
             {'type'    : 'text',
              'label'   : 'alpha',
              'default' : config_dict['alpha'],
              'is_child': False}
             ),

            ('intensity_dir',
             {'type'    : 'choice',
              'label'   : 'contrast dir',
              'choices' : ['single', 'both'],
              'default' : config_dict['intensity_dir'],
              'is_child': True}
             ),

            ('sf',
             {'type'    : 'text',
              'label'   : 'spatial frequency',
              'default' : config_dict['sf'],
              'is_child': True}
             ),

            ('phase',
             {'type'    : 'list',
              'label'   : 'phase (cycles)',
              'default' : config_dict['phase'],
              'is_child': True}
             ),

            ('phase_speed',
             {'type'    : 'list',
              'label'   : 'phase speed (hz)',
              'default' : config_dict['phase_speed'],
              'is_child': True}
             ),

            ('image_channel',
             {'type'    : 'choice',
              'label'   : 'color channel',
              'choices' : ['all', 'red', 'green', 'blue'],
              'default' : config_dict['image_channel'],
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
              'label'   : 'frequency (hz)',
              'default' : config_dict['period_mod'],
              'is_child': True}
             ),
        ])

        self.motion_param = OrderedDict([
            ('move_type',
             {'type'    : 'choice',
              'label'   : 'move type',
              'choices' : ['static', 'moving', 'table', 'random'],  # , 'jump'],
              'default' : config_dict['move_type'],
              'is_child': False,
              'children': {
                  'moving': ['speed', 'start_dir', 'num_dirs', 'start_radius',
                             'move_delay', 'ori_with_dir'],
                  'random': ['speed', 'travel_distance', 'move_seed'],
                  'table' : ['table_filename', 'start_dir', 'num_dirs',
                             'move_delay', 'ori_with_dir'],
                  # 'jump'  : ['num_jumps', 'jump_delay', 'move_seed'],
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

            ('ori_with_dir',
             {'type'    : 'choice',
              'label'   : 'orient with dir',
              'choices' : ['True', 'False'],
              'default' : config_dict['ori_with_dir'],
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

        self.global_default_param = OrderedDict([
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
              'label'   : 'center offset (pix)',
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
              'label'   : 'start trigger wait',
              'default' : config_dict['trigger_wait'],
              'is_child': False}
             ),

            ('background',
             {'type'    : 'list',
              'label'   : 'background (RGB)',
              'default' : config_dict['background'],
              'is_child': False}
             ),

            ('pref_dir',
             {'type'    : 'text',
              'label'   : 'preferred dir',
              'default' : config_dict['pref_dir'],
              'is_child': False}
             ),

            ('screen_num',
             {'type'    : 'choice',
              'label'   : 'screen number',
              'choices' : ['1', '2'],
              'default' : config_dict['screen_num'],
              'is_child': False}
             ),

            ('gamma_correction',
             {'type'    : 'choice',
              'label'   : 'gamma monitor',
              'choices' : ['default'] + self.get_gammas(),
              'default' : config_dict['gamma_correction'],
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
        ])


class TextCtrlTag(wx.TextCtrl):
    """
    Simple subclass of wx.TextCtrl for assigning ID tag to class to keep
    track of which parameter it was assigned to. Also method to set value.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag and tag2 if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        # tag2 used in list type parameters
        self.tag2 = kwargs.pop('tag2', None)
        wx.TextCtrl.__init__(self, *args, **kwargs)

    def set_value(self, value):
        """
        Method to change the value in the control.

        :param value: value to be changed to
        """
        self.SetValue(str(value))

    def set_editable(self, toggle, value=None):
        """
        Makes control not editable.
        """
        if not toggle:
            self.ChangeValue('table')
            self.SetEditable(False)

        if toggle:
            self.SetValue(value)
            self.SetEditable(True)


class ChoiceCtrlTag(wx.Choice):
    """
    Simple subclass of wx.Choice for assigning ID tag to class to keep
    track of which parameter it was assigned to. Also method to set value.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        wx.Choice.__init__(self, *args, **kwargs)

    def set_value(self, value):
        """
        Method to change the value in the control.

        :param value: value to be changed to
        """
        self.SetStringSelection(str(value))
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId,
                              self.Id)
        evt.SetEventObject(self)
        evt.SetString(str(value))
        self.GetParent().GetEventHandler().ProcessEvent(evt)

    def set_editable(self, toggle, value=None):
        """
        Makes control not editable.
        """
        if not toggle:
            self.Append('table')
            self.SetStringSelection('table')

        if toggle:
            self.SetStringSelection(value)
            self.Delete(self.GetCount() - 1)


class FilePickerCtrlTag(wx.FilePickerCtrl):
    """
    Simple subclass of wx.FilePickerCtrl for assigning ID tag to class to keep
    track of which parameter it was assigned to. Also method to set value,
    which requires category variable to know which panel control is in to
    edit parameters accordingly.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        self.category = kwargs.pop('category', None)
        wx.FilePickerCtrl.__init__(self, *args, **kwargs)

    def set_value(self, value):
        """
        Method to change the value in the control.

        :param value: value to be changed to
        """
        if value is not None:
            self.SetPath(value)
        # set path does not simulate event, so need to manually change
        # in parameters
        self.GetTopLevelParent().parameters.set_param_value(self.category,
                                                            self.tag,
                                                            value)


class TextCtrlValidator(wx.PyValidator):
    """
    Validator class to ensure proper entry of parameters.
    """
    def __init__(self):
        """
        normal constructor
        """
        wx.PyValidator.__init__(self)

    def Clone(self):
        """
        Standard cloner. All validators are required to implement the Clone()
        method.
        """
        return TextCtrlValidator()

    def Validate(self, win):
        """
        Validate contents of given TextCtrl.

        :param win:
        """
        text_box = self.GetWindow()
        value = text_box.GetValue()

        if value == 'table':
            return True

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


class InputPanel(wx.Panel):
    """
    Class for generic panel with input widgets and their labels. Parent class
    of SubPanel and GlobalPanel.
    """
    def __init__(self, params, parent, category):
        """
        Constructor
        :param params: dictionary of parameters
        :param parent: parent window of panel (notebook)
        :param category: category of parameters
        """
        # super instantiation
        super(InputPanel, self).__init__(parent)

        # instance attributes
        self.frame = parent.GetTopLevelParent()
        self.parameters = self.frame.parameters
        self.category = category
        self.params = params

        # dictionary for list of associated SubPanels to make proper show and
        # hide calls
        self.sub_panel_dict = {}

        # dictionary of all controls, including subpanel controls
        self.all_controls = self.frame.all_controls

        # counters for list and pos in sizer, accessed by SubPanel
        self.list_counter = 0
        self.grid_counter = 0

        # sizer for controls and labels, accessed by SubPanel
        self.grid_sizer = wx.GridBagSizer(hgap=5, vgap=5)

        # create inputs and add to sizers
        self.create_inputs(category)

        # nest and place sizers
        panel_sizer = wx.BoxSizer()
        panel_sizer.Add(self.grid_sizer,
                        proportion=1,
                        flag=wx.ALL | wx.EXPAND,
                        border=10)

        # set sizer for panel
        self.SetSizer(panel_sizer)

    def create_inputs(self, category):
        """
        Method to recursively generate label and input widgets.
        Checks if param is child of another and only generates
        parent params, then generates subpanel with associated child
        params. Differentiates between input types (text, dropdown,
        list (i.e. multiple text fields).

        :param category:
        """

        # iterate through params in param dict
        for param, param_info in self.params.iteritems():
            # only generate fields for params that aren't children
            if not param_info['is_child']:
                # label widget
                label = wx.StaticText(self, label=param_info['label'] + ':')

                param_type = param_info['type']

                # input widgets, depending on type
                if param_type == 'text':
                    # make control
                    ctrl = TextCtrlTag(self,
                                       size=(120, -1),
                                       tag=param,
                                       value=str(param_info['default']),
                                       validator=TextCtrlValidator())
                    # add control to dict of all controls
                    self.all_controls[param] = ctrl
                    # bind events to methods
                    self.Bind(wx.EVT_TEXT, self.input_update, ctrl)
                    self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click, ctrl)

                elif param_type == 'choice':
                    ctrl = ChoiceCtrlTag(self,
                                         tag=param,
                                         choices=param_info['choices'])
                    self.all_controls[param] = ctrl

                    # on Win32, choice still defaults to blank, so manually
                    # set selection to default for aesthetic reasons
                    ctrl.SetStringSelection(str(param_info['default']))

                    self.Bind(wx.EVT_CHOICE, self.input_update, ctrl)
                    self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click, ctrl)

                elif param_type == 'path':
                    ctrl = FilePickerCtrlTag(self,
                                             tag=param,
                                             category=self.category,
                                             message='Path to file',
                                             style=wx.FLP_USE_TEXTCTRL |
                                                   wx.FLP_SMALL)
                    self.all_controls[param] = ctrl
                    self.Bind(wx.EVT_FILEPICKER_CHANGED, self.input_update,
                              ctrl)

                elif param_type == 'list':
                    # get length of list for sizer and TextCtrl sizing
                    length = len(param_info['default'])
                    # sizer for adding text boxes into grid
                    list_sizer = wx.GridSizer(rows=1, cols=length, hgap=5)

                    # iterate through number of fields in each list and
                    # create a TextCtrl for each, with tag2 as the position
                    # of the input in the param list
                    # also resize TextCtrl so lengths match up for aesthetic
                    # purposes
                    # TODO: find a better way to size list TextCtrl
                    for i in range(length):
                        ctrl = TextCtrlTag(self,
                                           tag=param,
                                           tag2=i,
                                           size=((120 / length - (5 * (
                                               length - 1)) / length), -1),
                                           value=str(param_info['default'][i]),
                                           validator=TextCtrlValidator())

                        ctrl_name = param + '[' + str(i) + ']'
                        self.all_controls[ctrl_name] = ctrl

                        # add to sizer
                        list_sizer.Add(ctrl)
                        self.Bind(wx.EVT_TEXT, self.input_update, ctrl)
                        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click, ctrl)

                    # set ctrl to sizer in order to be added to grid_sizer
                    ctrl = list_sizer

                # add widgets to sizer
                self.grid_sizer.Add(label, pos=(self.grid_counter, 0))
                self.grid_sizer.Add(ctrl, pos=(self.grid_counter, 1))

                # increment counters
                self.list_counter += 1
                self.grid_counter += 1

            # check if param has child param
            if 'children' in param_info:
                # create a new dictionary in sub panel dict for that parameter
                # because some panels have more than one subpanel, and the
                # proper subpanel needs to be referenced on calls to Show()
                # and Hide()
                self.sub_panel_dict[param] = {}

                # single box sizer so that subpanels can occupy the same
                # space in the panel's gridbox sizer
                subpanel_sizer = wx.BoxSizer(wx.VERTICAL)

                # iterate through the dictionary of child params
                for choice, child_params in param_info['children'].iteritems():
                    # create new ordered dict to hold only child params
                    child_param_dict = OrderedDict()

                    # iterate through list of child params and create copy of
                    # dict entry found in param dict. Need to make copy or
                    # else changes will make changes wrong dict
                    for child_param in child_params:
                        child_param_dict[child_param] = deepcopy(
                            self.params[child_param])

                    # iterate through new child param dict and reset is_child
                    for values in child_param_dict.itervalues():
                        values['is_child'] = False

                    # make sub panel with new dict
                    self.sub_panel_dict[param][choice] = InputPanel(
                        child_param_dict, self, category)

                # add panels to subpanel sizer
                for panel in self.sub_panel_dict[param].itervalues():
                    subpanel_sizer.Add(panel, proportion=1)

                # add subpanel sizer to panel sizer, spanning both columns
                self.grid_sizer.Add(subpanel_sizer,
                                    pos=(self.grid_counter, 0),
                                    span=(1, 2))

                # increment grid counter
                self.grid_counter += 1

    def input_update(self, event):
        """
        Method for updating parameters on changes to input controls

        :param event: wxPython event, passed by binder
        """
        self.Validate()

        # Get tag of object (which is param name)
        param = event.GetEventObject().tag

        # if dir selector, get new path
        if self.params[param]['type'] == 'path':
            value = event.GetPath()
        else:
            # else get the new value from the widget
            value = event.GetString()

        # if in grid, leave choice as table and don't do anything
        if isinstance(event.GetEventObject(), ChoiceCtrlTag):
            if param in self.frame.grid.control_dict:
                event.Skip()
                event.GetEventObject().SetStringSelection('table')
                return


        # if a list type param, change the appropriate list item by getting
        # tag2 (list index)
        if self.params[param]['type'] == 'list':
            index = event.GetEventObject().tag2
            self.parameters.set_param_value(self.category, param, value,
                                            index=index)

        else:
            self.parameters.set_param_value(self.category, param, value)

        # hide/show panels if necessary
        if 'children' in self.params[param]:
            # iterate through all the subpanel and show/hide as needed
            for item in self.params[param]['children']:
                if item == value:
                    self.sub_panel_dict[param][item].Show()
                else:
                    self.sub_panel_dict[param][item].Hide()
            # redraw
            self.Fit()

        # some params need to edit global defaults of StimProgram on the fly
        # instead of at window instantiation
        global_params = self.parameters.get_global_params()

        if param == 'log':
            StimProgram.GlobalDefaults['log'] = global_params['log']

        if param == 'trigger_wait':
            StimProgram.GlobalDefaults['trigger_wait'] = \
                global_params['trigger_wait']

        if param == 'protocol_reps':
            StimProgram.GlobalDefaults['protocol_reps'] = \
                global_params['protocol_reps']

        if param == 'pref_dir':
            StimProgram.GlobalDefaults['pref_dir'] = \
                global_params['pref_dir']

        if param == 'background':
            StimProgram.MyWindow.change_color(global_params['background'])

    def on_right_click(self, event):
        """
        Method for passing parameter to table to be added.

        :param event:
        """
        ctrl = event.GetEventObject()
        param = ctrl.tag

        try:
            if ctrl.tag2 is not None:
                param = param + '[' + str(ctrl.tag2) + ']'
        except AttributeError:
            pass

        self.frame.grid.add_to_grid(param)


class GlobalPanel(InputPanel):
    """
    Subclass of InputPanel, contains a few aesthetic changes in its init
    since not part of a notebook.
    """
    def __init__(self, parent, params, category):
        # super initiation
        super(GlobalPanel, self).__init__(parent, params, category)

        # instance variables
        self.frame = self.GetTopLevelParent()
        self.parameters = self.frame.parameters

        # move items down a few slots to insert spacers and titles
        for item in reversed(self.grid_sizer.GetChildren()):
            x, y = item.GetPosTuple()
            x += 2
            pos = x, y
            item.SetPos(pos)

        # title
        self.title = wx.StaticText(self, label="Global Defaults")
        self.grid_sizer.Add(self.title, pos=(0, 0))

        # global file
        self.globals_file = os.path.abspath(
            '.\psychopy\data\global_defaults_new.txt')

        # check if file exists, and if so load different options
        if os.path.exists(self.globals_file):
            with open(self.globals_file, 'rb') as f:
                global_dict = cPickle.load(f)

            defaults_list = global_dict.keys()

        else:
            defaults_list = []

        self.which_default = ChoiceCtrlTag(self, tag='defaults',
                                           choices=sorted(defaults_list))
        self.Bind(wx.EVT_CHOICE, self.on_default_select, self.which_default)
        self.grid_sizer.Add(self.which_default, pos=(0, 1))

        # if global default in ini, select
        if self.frame.gui_params['defaults'] is not None:
            self.which_default.set_value(self.frame.gui_params['defaults'])

        # save button
        self.save_default = wx.Button(self, size=(-1, -1), id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.on_default_save, self.save_default)
        self.grid_sizer.Add(self.save_default, pos=(1, 0))

        # delete button
        self.delete_default = wx.Button(self, size=(-1, -1), label='Delete')
        self.Bind(wx.EVT_BUTTON, self.on_default_delete, self.delete_default)
        self.grid_sizer.Add(self.delete_default, pos=(1, 1))

    def on_default_save(self, event):
        """
        Saves global default parameters.

        :param event:
        """
        # popup dialog to enter save name
        save_name_dialog = wx.TextEntryDialog(self, 'save name')

        # to exit out of popup on cancel
        if save_name_dialog.ShowModal() == wx.ID_CANCEL:
            return

        # get entered save name
        save_name = save_name_dialog.GetValue()

        # get params from parameters
        params_to_save = self.parameters.get_global_params()

        # data folder
        data_folder = os.path.abspath('./psychopy/data/')

        # create folder if not present
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        # get saved globals if present
        if os.path.exists(self.globals_file):
            with open(self.globals_file, 'rb') as f:
                global_dict = cPickle.load(f)

        # leave dict empty otherwise
        else:
            global_dict = {}

        # if new save, add to dropdown
        if save_name not in global_dict.keys():
            self.which_default.Append(save_name)

        # switch dropdown to save
        self.which_default.SetStringSelection(save_name)

        # add entry to global dict and redump to file
        global_dict[save_name] = params_to_save

        with open(self.globals_file, 'wb') as f:
            cPickle.dump(global_dict, f)

    def on_default_delete(self, event):
        """
        Deletes global default parameters.

        :param event:
        """
        # get which entry is selected
        selected = self.which_default.GetStringSelection()

        if selected != '':

            # get list of saves from file
            with open(self.globals_file, 'rb') as f:
                global_dict = cPickle.load(f)

            # remove from dict
            del global_dict[selected]

            # redump dict to file
            with open(self.globals_file, 'wb') as f:
                cPickle.dump(global_dict, f)

            # add blank spot in control to switch to
            self.which_default.Append('')
            self.which_default.SetStringSelection('')

            # delete from control deleted item
            index = self.which_default.GetItems().index(selected)
            self.which_default.Delete(index)

            # delete blank so it can't be selected. Stays currently selected
            # though
            index = self.which_default.GetItems().index('')
            self.which_default.Delete(index)

    def on_default_select(self, event):
        """
        Populates global default panel based on saved globals.

        :param event:
        """
        selected = event.GetString()

        # get params to load
        with open(self.globals_file, 'rb') as f:
            params_to_load = cPickle.load(f)[selected]

        for param, control in self.frame.all_controls.iteritems():
            try:
                # if not a list text control
                if param[-1] != ']':
                    control.set_value(params_to_load[param])
                else:
                    index = int(param[-2])
                    control.set_value(params_to_load[param[:-3]][index])

            # if not in either dictionary, leave as is
            except KeyError:
                pass


class ListPanel(wx.Panel):
    """
    Panel that contains list of stims to run along with add/remove buttons
    and up/down buttons.
    """
    def __init__(self, parent):
        """Constructor
        """
        super(ListPanel, self).__init__(parent)

        # instance attributes
        self.frame = parent.GetTopLevelParent()
        self.parameters = self.frame.parameters
        self.stims_to_run = []

        # panel title and its own sizer for proper border spacing
        title = wx.StaticText(self, label='stims to run')
        title_sizer = wx.BoxSizer()
        title_sizer.Add(title, flag=wx.TOP | wx.BOTTOM, border=7)

        # sizer for panel
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # add title to top of panel sizer
        panel_sizer.Add(title_sizer,
                        proportion=0,
                        flag=wx.BOTTOM | wx.LEFT,
                        border=3)

        # list control widget
        self.list_control = wx.ListCtrl(self,
                                        size=(200, -1),
                                        style=wx.LC_REPORT | wx.SUNKEN_BORDER)

        # add columns to list control
        self.list_control.InsertColumn(0, 'Fill')
        self.list_control.InsertColumn(1, 'Shape')
        self.list_control.InsertColumn(2, 'Type')
        self.list_control.InsertColumn(3, 'Trigger')

        # add list control to panel sizer
        panel_sizer.Add(self.list_control,
                        proportion=1,
                        flag=wx.EXPAND)

        # up down buttons
        self.up_button = wx.Button(self, label='Move up')
        self.down_button = wx.Button(self, label='Move down')

        # sizer for up and down buttons
        up_down_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add buttons to sizer
        up_down_sizer.Add(self.up_button,
                          proportion=1,
                          flag=wx.LEFT | wx.RIGHT,
                          border=5)

        up_down_sizer.Add(self.down_button,
                          proportion=1,
                          flag=wx.LEFT | wx.RIGHT,
                          border=5)

        # add up down sizer to panel sizer
        panel_sizer.Add(up_down_sizer,
                        proportion=0,
                        flag=wx.TOP | wx.ALIGN_CENTER_HORIZONTAL |
                             wx.ALIGN_CENTER_VERTICAL,
                        border=5)

        # add remove buttons
        self.add_button = wx.Button(self, id=wx.ID_ADD)
        self.remove_button = wx.Button(self, id=wx.ID_REMOVE)

        # sizer for add and remove buttons
        add_remove_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add buttons to sizer
        add_remove_sizer.Add(self.add_button,
                             proportion=1,
                             flag=wx.LEFT | wx.RIGHT,
                             border=5)

        add_remove_sizer.Add(self.remove_button,
                             proportion=1,
                             flag=wx.LEFT | wx.RIGHT,
                             border=5)

        # add up down sizer to panel sizer
        panel_sizer.Add(add_remove_sizer,
                        proportion=0,
                        flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL |
                             wx.ALIGN_CENTER_VERTICAL,
                        border=5)

        # button binders
        self.Bind(wx.EVT_BUTTON, self.on_up_button, self.up_button)
        self.Bind(wx.EVT_BUTTON, self.on_down_button, self.down_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_button, self.add_button)
        self.Bind(wx.EVT_BUTTON, self.on_remove_button, self.remove_button)

        # sizer for double click on list item
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_double_click,
                  self.list_control)

        # set panel sizer for panel
        self.SetSizer(panel_sizer)

    def convert_stim_type(self, stim_type):
        """
        Converts stim_type label to class names and back

        :param stim_type: string to be converted
        :return: converted string
        """

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

        elif stim_type == 'static':
            stim_type = 'StaticStim'
        elif stim_type == 'moving':
            stim_type = 'MovingStim'
        elif stim_type == 'random':
            stim_type = 'RandomlyMovingStim'
        elif stim_type == 'table':
            stim_type = 'TableStim'
        elif stim_type == 'jump':
            stim_type = 'ImageJumpStim'

        return stim_type

    def on_add_button(self, event):
        """
        Makes call to add to list with proper params

        :param event:
        """
        param_dict = self.parameters.get_merged_params()
        stim_type = param_dict.pop('move_type')

        self.add_to_list(stim_type, param_dict)

    def add_to_list(self, stim_type, param_dict, insert_pos=None):
        """
        Adds stim to list of stims to run, as a bew stiminfo class

        :param stim_type:
        :param param_dict:
        :param insert_pos: at which position in list to insert stim. Used
        when moving stims up and down
        :return:
        """

        if insert_pos is None:
            insert_pos = self.list_control.GetItemCount()

        # info for list
        fill = param_dict['fill_mode']
        shape = param_dict['shape']
        trigger = str(param_dict['trigger'])

        # add info about stim to list
        self.list_control.InsertStringItem(insert_pos, fill)
        self.list_control.SetStringItem(insert_pos, 1, shape)
        self.list_control.SetStringItem(insert_pos, 2, stim_type)
        self.list_control.SetStringItem(insert_pos, 3, trigger)
        # resize columns to fit
        self.list_control.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.list_control.SetColumnWidth(3, wx.LIST_AUTOSIZE)

        # convert from stim type label to StimProgram instance
        stim_type = self.convert_stim_type(stim_type)

        # stim info instance to store
        stim_info = StimProgram.StimInfo(stim_type, param_dict, insert_pos)

        # add to list of stims to run
        if insert_pos is not None:
            self.stims_to_run.insert(insert_pos, stim_info)
        else:
            self.stims_to_run.append(stim_info)

        # deselect all so most in list and select most recently added
        while self.list_control.GetSelectedItemCount() != 0:
            self.list_control.Select(self.list_control.GetFirstSelected(), on=0)
        self.list_control.Select(insert_pos)

    def on_remove_button(self, event):
        """
        Removes stims from stim list. If none selected, clears all.

        :param event:
        """
        # if any selected, iterate through and delete
        if self.list_control.GetSelectedItemCount() > 0:
            for i in range(self.list_control.GetSelectedItemCount()):
                selected = self.list_control.GetFirstSelected()
                # remove from stims to run
                del self.stims_to_run[selected]
                # remove from list
                self.list_control.DeleteItem(selected)

            # reset stim numbers in stims to run
            for i, stim in enumerate(self.stims_to_run):
                stim.number = i

        else:
            self.list_control.DeleteAllItems()
            # clear stims to run
            del self.stims_to_run[:]

    def on_up_button(self, event):
        """
        Moves a stim up in the list by removing it and reinserting it into
        proper position.

        :param event:
        """
        # only move if only 1 stim selected
        if self.list_control.GetSelectedItemCount() == 1:
            index = self.list_control.GetFirstSelected()
            # don't move up if already at top
            if index > 0:
                # get params
                stim = self.stims_to_run[index]
                stim_type = self.convert_stim_type(stim.stim_type)
                param_dict = stim.parameters

                # remove
                self.on_remove_button(event)

                # readd
                self.add_to_list(stim_type, param_dict, index - 1)

                # reset stim numbers in stims to run
                for i, stim in enumerate(self.stims_to_run):
                    stim.number = i

    def on_down_button(self, event):
        """
        Moves a stim down in the list by removing it and reinserting it into
        proper position.

        :param event:
        """
        # only move if only 1 stim selected
        if self.list_control.GetSelectedItemCount() == 1:
            index = self.list_control.GetFirstSelected()
            # don't move up if already at bottom
            if index < self.list_control.GetItemCount() - 1:
                # get params
                stim = self.stims_to_run[index]
                stim_type = self.convert_stim_type(stim.stim_type)
                param_dict = stim.parameters

                # remove
                self.on_remove_button(event)

                # readd
                self.add_to_list(stim_type, param_dict, index + 1)

                # reset stim numbers in stims to run
                for i, stim in enumerate(self.stims_to_run):
                    stim.number = i

    def on_double_click(self, event):
        """
        Loads params from list on double click

        :param event:
        """
        selected = self.list_control.GetFirstSelected()
        stim = self.stims_to_run[selected]
        # copy so adding move type doesn't affect StimInfo instance
        params = deepcopy(stim.parameters)

        stim_type = self.convert_stim_type(stim.stim_type)
        params['move_type'] = stim_type

        for param, control in self.frame.all_controls.iteritems():
            try:
                # if not a list text control
                if param[-1] != ']':
                    control.set_value(params[param])
                else:
                    index = int(param[-2])
                    control.set_value(params[param[:-3]][index])

            # if not in either dictionary, leave as is
            except KeyError:
                pass

        print '\nStim params populated'


class DirPanel(wx.Panel):
    """
    Class for file browser panel.
    """
    def __init__(self, parent):
        """
        Constructor.

        :param parent:
        """
        # super instantiation
        super(DirPanel, self).__init__(parent)

        # instance attributes
        self.frame = parent.GetTopLevelParent()
        self.parameters = self.frame.parameters

        # sizer for panel
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # file browser
        default_dir = self.frame.gui_params['saved_stim_dir']
        self.browser = wx.FileCtrl(self,
                                   wildCard='*.txt',
                                   size=(200, -1),
                                   defaultDirectory=default_dir)

        # add browser to panel
        panel_sizer.Add(self.browser,
                        proportion=1,
                        flag=wx.EXPAND)

        # make buttons
        self.save_button = wx.Button(self, id=wx.ID_SAVE)
        self.load_button = wx.Button(self, label='Load')

        # button sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add buttons to sizer
        button_sizer.Add(self.save_button,
                         proportion=1,
                         flag=wx.LEFT | wx.RIGHT,
                         border=5)

        button_sizer.Add(self.load_button,
                         proportion=1,
                         flag=wx.LEFT | wx.RIGHT,
                         border=5)

        # add button sizer to panel sizer
        panel_sizer.Add(button_sizer,
                        border=5,
                        flag=wx.BOTTOM | wx.TOP |
                             wx.ALIGN_CENTER_HORIZONTAL |
                             wx.ALIGN_CENTER_VERTICAL)

        # event binders
        self.Bind(wx.EVT_BUTTON, self.on_save_button, self.save_button)
        self.Bind(wx.EVT_BUTTON, self.on_load_button, self.load_button)
        self.Bind(wx.EVT_FILECTRL_FILEACTIVATED, self.on_double_click,
                  self.browser)

        # set sizer to panel
        self.SetSizer(panel_sizer)

    def on_save_button(self, event):
        """
        Saves current list of stims to text file.

        :param event:
        """
        default_dir = os.path.abspath('./psychopy/stims/')

        # popup save dialog
        save_dialog = wx.FileDialog(self.frame,
                                    message='File path',
                                    defaultDir=default_dir,
                                    wildcard='*.txt',
                                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        # to exit out of popup on cancel button
        if save_dialog.ShowModal() == wx.ID_CANCEL:
            return

        # get list of stims that need to be saved
        to_save = []
        stims = self.frame.list_panel.stims_to_run

        for i, stim in enumerate(stims):
            params = deepcopy(stim.parameters)
            # add move type back in to parameters
            params['move_type'] = stim.stim_type
            # add to save list
            to_save.append(params)

        # get path from save dialog
        path = save_dialog.GetPath()

        # open text file in binary mode to dump
        with open(path, 'wb') as f:
            cPickle.dump(to_save, f)

        # refresh file browser to show new saved file
        # ugly way of doing this
        self.browser.ShowHidden(True)
        self.browser.ShowHidden(False)

    def on_load_button(self, event):
        """
        Loads stims from text file.

        :param event:
        """
        # get path from browser
        path = self.browser.GetPath()

        is_log = os.path.split(os.path.split(os.path.dirname(path))[0])[1] ==\
                 'logs'

        # if not log file, open and load pickle data
        if not is_log:
            try:
                with open(path, 'rb') as f:
                    to_load = cPickle.load(f)
            except IOError:
                print '\nNo file selected. Please select file.'
                return

        # if log file, need to seek to end to find the pickle data
        else:
            try:
                with open(path, 'rb') as f:
                    # iterate through lines to look for pickle header
                    next_is_pickle = False
                    to_load = ''

                    for line in f:
                        if next_is_pickle:
                            to_load += line

                        # need to strip newline character
                        line = line.rstrip()
                        if line == '#BEGIN PICKLE#':
                            next_is_pickle = True

                    to_load = cPickle.loads(to_load)

            except ValueError:
                print '\nERROR: file not a properly formatted parameter file'
                return

        # load stims in to list panel
        for params in to_load:
            # take back out move type
            stim_type = params.pop('move_type')

            # convert from StimProgram instance label to stim type
            stim_type = self.frame.list_panel.convert_stim_type(stim_type)

            self.frame.list_panel.add_to_list(stim_type, params)

        print '\nStim(s) saved'

    def on_double_click(self, event):
        """
        If log file, opens, else loads.

        :param event:
        """
        path = self.browser.GetPath()

        is_log = os.path.split(os.path.split(os.path.dirname(path))[0])[1] ==\
                 'logs'

        if is_log:
            if platform == 'darwin':
                os.startfile(path)
            elif platform == 'win32':
                os.system('open ' + path)

        else:
            self.on_load_button(event)


class MyGrid(wx.Frame):
    """
    Class for grid window.
    """
    def __init__(self, parent):
        """
        Constructor.

        :param parent:
        :return:
        """
        # necessary call to super
        super(MyGrid, self).__init__(parent, title='Table')

        # instance attributes
        self.frame = parent
        self.parameters = self.frame.parameters
        self.grid_shown = False
        self.control_dict = {}

        # panel to hold everything
        panel = wx.Panel(self)

        # instantiate grid
        self.grid = wx.grid.Grid(panel)
        self.grid.CreateGrid(0, 0)

        # sizer for grid
        grid_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer.Add(self.grid, proportion=1, flag=wx.EXPAND)

        # set sizer
        panel.SetSizer(grid_sizer)

        # bind grid events
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK,
                  self.on_grid_label_right_click)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,
                  self.on_grid_cell_right_click)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                  self.on_grid_cell_changed)

        # catch close to only hide grid
        self.Bind(wx.EVT_CLOSE, self.on_close_button)

    def show_grid(self):
        """
        Method to show grid. Unminimizes and brings to front.
        """
        self.Iconize(False)
        self.Show()
        self.Raise()
        self.grid_shown = True

    def hide_grid(self):
        """
        Method to hide grid.
        """
        self.Hide()
        self.grid_shown = False

    def on_close_button(self, event):
        """
        Catches close in order to only hide. Otherwise frame object is
        deleted and loses all data.

        :param event:
        """
        self.hide_grid()

    def add_to_grid(self, param):
        """
        Adds column to table and prevents editing of control.

        :param param:
        """
        ctrl = self.frame.all_controls[param]

        if param not in self.control_dict and ctrl.GetParent().category != \
                'global':
            # add column to grid
            self.grid.ClearSelection()
            self.grid.AppendCols(1)
            self.grid.SetGridCursor(0, self.grid.GetNumberCols()-1)
            self.grid.SetColLabelValue(self.grid.GetNumberCols()-1, param)

            # get value of control
            try:
                value = self.parameters.get_param_value(
                    ctrl.GetParent().category, param)
            except:
                index = int(param[-2])
                value = self.parameters.get_param_value(
                    ctrl.GetParent().category, param[:-3], index)

            value = str(value)

            # if no other rows, add some, and populate control dict
            if self.grid.NumberCols == 1:
                self.grid.AppendRows(5)
                self.control_dict[param] = [None] * 5
            else:
                self.control_dict[param] = [None] * (self.grid.GetNumberRows())

            self.control_dict[param][0] = value

            ctrl.set_editable(False)

            self.grid.SetCellValue(0, self.grid.GetNumberCols()-1, value)

            print self.control_dict

        # if already in grid
        else:
            self.grid.ClearSelection()

            # highlight column
            for i in range(self.grid.GetNumberCols()):
                if self.grid.GetColLabelValue(i) == param:
                    self.grid.SelectCol(i)
                    self.grid.SetGridCursor(0, i)

        self.show_grid()

    def on_grid_cell_changed(self, event):
        """
        Updates control dict when values in cells are changed.

        :param event:
        """
        row = event.GetRow()
        col = event.GetCol()
        param = self.grid.GetColLabelValue(col)

        value = self.grid.GetCellValue(row, col)
        if value == '':
            value = None

        self.control_dict[param][row] = value

        # if in last row, add more rows
        if row == self.grid.GetNumberRows() - 1:
            evt = wx.grid.GridEvent(self.grid.GetId(),
                                    wx.grid.wxEVT_GRID_LABEL_RIGHT_CLICK,
                                    self,
                                    row=-1,
                                    col=-1)
            self.GetEventHandler().ProcessEvent(evt)

            self.grid.MoveCursorDown(False)

    def on_grid_label_right_click(self, event):
        """
        Adds more rows if top left corner right clicked. Deletes row/column if
        row/column header right clicked.

        :param event:
        """
        row = event.GetRow()
        col = event.GetCol()

        # column headers
        if row == -1:
            # leftmost column
            if col == -1:
                self.grid.AppendRows(5)
                # add to control dict lists
                for value in self.control_dict.itervalues():
                        value.extend([None] * 5)

            # any other column header
            else:
                # make control editable and set value
                param = self.grid.GetColLabelValue(col)
                old_value = self.control_dict[param][0]
                self.frame.all_controls[param].set_editable(True, value=old_value)

                # remove column and from control dict
                self.grid.DeleteCols(col, 1)
                del self.control_dict[param]

                # if no more columns, delete rows
                if self.grid.GetNumberCols() == 0:
                    self.grid.DeleteRows(0, numRows=self.grid.GetNumberRows())
                    self.Hide()

        # row headers
        elif col == -1:
            for value in self.control_dict.itervalues():
                del value[row]

            self.grid.DeleteRows(row, 1)

    def on_grid_cell_right_click(self, event):
        """
        Removes contents of cell.

        :param event:
        """
        row = event.GetRow()
        col = event.GetCol()

        param = self.grid.GetColLabelValue(col)

        self.Grid.SetCellValue(row, col, '')
        self.control_dict[param][row] = None


class MyFrame(wx.Frame):
    """
    Class for generating frame. Instantiates parameters, notebook, and panels.
    """
    def __init__(self):
        """
        Constructor. Creates and lays out panels in sizers, finally hiding
        unnecessary subpanels.
        """

        # super initiation
        super(MyFrame, self).__init__(None, title="Stimulus Program")

        # instantiate parameters
        self.parameters = Parameters()
        self.gui_params = self.parameters.get_gui_params()

        # instance attributes
        self.win_open = False
        self.all_controls = {}
        self.do_break = False

        # make grid
        self.grid = MyGrid(self)

        # notebook to hold input panels
        self.input_nb = wx.Notebook(self)

        # instantiate panels with notebook as parent
        self.panel_shape = InputPanel(self.parameters.get_params('shape'),
                                      self.input_nb,
                                      'shape')

        self.panel_timing = InputPanel(self.parameters.timing_param,
                                       self.input_nb,
                                       'timing')

        self.panel_move = InputPanel(self.parameters.motion_param,
                                     self.input_nb,
                                     'motion')

        self.panel_fill = InputPanel(self.parameters.fill_param,
                                     self.input_nb,
                                     'fill')

        # add panels to notebook
        self.input_nb.AddPage(self.panel_shape, "Shape")
        self.input_nb.AddPage(self.panel_timing, "Time")
        self.input_nb.AddPage(self.panel_fill, " Fill ")
        self.input_nb.AddPage(self.panel_move, "Motion")

        # instantiate global panel
        self.panel_global = GlobalPanel(self.parameters.global_default_param,
                                        self, 'global')

        # sizer to hold notebook and global panel
        panel_row = wx.BoxSizer(wx.HORIZONTAL)

        # add notebook panel and global panel to sizer
        panel_row.Add(self.input_nb, proportion=1, flag=wx.EXPAND)
        panel_row.Add(self.panel_global, proportion=1, flag=wx.EXPAND)

        # create buttons
        self.run_button = wx.Button(self, label="Run")
        self.stop_button = wx.Button(self, label="Stop")
        self.win_button = wx.Button(self, label="Window")
        self.exit_button = wx.Button(self, label="Exit")

        # binders
        self.Bind(wx.EVT_BUTTON, self.on_run_button, self.run_button)
        self.Bind(wx.EVT_BUTTON, self.on_win_button, self.win_button)
        self.Bind(wx.EVT_BUTTON, self.on_stop_button, self.stop_button)
        self.Bind(wx.EVT_BUTTON, self.on_exit_button, self.exit_button)

        # sizer for buttons under panel_row
        stim_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add to sizer
        stim_buttons_sizer.Add(self.run_button,
                               proportion=1,
                               border=5,
                               flag=wx.LEFT | wx.RIGHT)

        stim_buttons_sizer.Add(self.stop_button,
                               proportion=1,
                               border=5,
                               flag=wx.LEFT | wx.RIGHT)

        stim_buttons_sizer.Add(self.win_button,
                               proportion=1,
                               border=5,
                               flag=wx.LEFT | wx.RIGHT)

        stim_buttons_sizer.Add(self.exit_button,
                               proportion=1,
                               border=5,
                               flag=wx.LEFT | wx.RIGHT)

        # sizer for input and global panels and buttons
        panel_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # add buttons and panels
        panel_button_sizer.Add(panel_row, proportion=1, flag=wx.EXPAND)
        panel_button_sizer.Add(stim_buttons_sizer,
                               border=5,
                               flag=wx.BOTTOM | wx.TOP |
                                    wx.ALIGN_CENTER_HORIZONTAL |
                                    wx.ALIGN_CENTER_VERTICAL)

        # instantiate list and dir panel
        self.list_panel = ListPanel(self)
        self.dir_panel = DirPanel(self)

        # frame sizer to hold panel button sizer and list panel
        frame_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add list and dir panel and panel button sizer to frame sizer
        frame_sizer.Add(self.dir_panel,
                        proportion=1,
                        flag=wx.EXPAND | wx.RIGHT,
                        border=5)

        frame_sizer.Add(self.list_panel,
                        proportion=1,
                        flag=wx.EXPAND | wx.RIGHT,
                        border=5)

        frame_sizer.Add(panel_button_sizer)

        # status bar
        self.CreateStatusBar(1)
        self.SetStatusText('hi there')

        # hide all subpanels
        for panel in self.input_nb.GetChildren():
            for param in panel.sub_panel_dict.iterkeys():
                for subpanel in panel.sub_panel_dict[param].iterkeys():
                    panel.sub_panel_dict[param][subpanel].Hide()

        # set sizer
        self.SetSizer(frame_sizer)
        frame_sizer.Fit(self)

        # show/hide appropriate subpanels
        for panel in self.input_nb.GetChildren():
            for param in panel.sub_panel_dict.iterkeys():
                for subpanel in panel.sub_panel_dict[param].iterkeys():
                    if subpanel != panel.params[param]['default']:
                        panel.sub_panel_dict[param][subpanel].Hide()
                    else:
                        panel.sub_panel_dict[param][subpanel].Show()
                        panel.Fit()

        # change background color to match panels on win32
        if platform == 'win32':
            self.SetBackgroundColour(wx.NullColour)

        # draw frame
        self.Show()

    def on_run_button(self, event):
        if len(self.list_panel.stims_to_run) != 0:
            if self.win_open:
                self.on_stop_button(event)

            else:
                self.on_win_button(event)

            self.run()
        else:
            print 'Please add stims.'

    def run(self):
        """
        Method for running stims.
        """
        # try/except, so that uncaught errors thrown by StimProgram can be
        # caught and thrown to avoid hanging.
        try:
            self.SetStatusText('running...')
            fps, time, time_stamp = StimProgram.main(
                self.list_panel.stims_to_run)

            if time != 'error':
                status_text = 'Last run: {0:.2f} fps, '.format(fps) \
                                   + '{0:.2f} seconds.'.format(time)

                if time_stamp is not None:
                    status_text += ' Timestamp: {}'.format(time_stamp)

                self.SetStatusText(status_text)
            else:
                self.SetStatusText(fps)

        except:
            raise

    def on_win_button(self, event):
        """
        Method for toggling stim window. Makes call to StimProgram. Gets
        various params from global panel.

        :param event: event passed by binder
        :return:
        """
        if self.win_open:
            self.on_stop_button(event)
            StimProgram.MyWindow.close_win()
            self.win_open = False

        else:
            global_defaults = self.parameters.get_global_params()
            # adjust screen number to zero based index
            global_defaults['screen_num'] -= 1

            # offset needs to be passed as a scale relative to display size
            global_defaults['offset'] = [float(x) / y * 2 for x, y in zip(
                global_defaults['offset'],
                global_defaults['display_size'])]

            self.win_open = True
            # pass global defaults to stim program
            StimProgram.GlobalDefaults(**global_defaults)
            # make window
            StimProgram.MyWindow.make_win()

    def on_stop_button(self, event):
        """
        Method for stopping stim. Makes call to StimProgram.

        :param event: event passed by binder
        """
        self.do_break = True
        StimProgram.MyWindow.should_break = True

    def on_exit_button(self, event):
        """
        Closes application.

        :param event: event passed by binder
        """
        if self.win_open:
            self.on_stop_button(event)
            StimProgram.MyWindow.close_win()
        self.Close()


def main():
    """
    Main function to start GUI.
    """
    # instantiate app
    global app
    app = wx.App(False)
    # instantiate window
    frame = MyFrame()
    # run app
    app.MainLoop()

if __name__ == "__main__":
    main()
