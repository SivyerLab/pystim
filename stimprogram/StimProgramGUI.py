"""
GUI for StimProgram
"""

# Copyright (C) 2016 Alexander Tomlinson
# Distributed under the terms of the GNU General Public License (GPL).

# must first turn pyglet shadow windows off to avoid conflict between wxPython
# and psychopy.visual on OSX
import pyglet
pyglet.options['shadow_window'] = False

from GammaCorrection import GammaValues  # unused, but necessary for pickling
from collections import OrderedDict
from ast import literal_eval
from copy import deepcopy
from sys import platform
from PIL import Image
import ConfigParser
import StimProgram
import subprocess
import traceback
import cPickle
import json
import os

import wx.lib.agw.multidirdialog as mdd
import wx, wx.grid


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
        self.stim_params = None

        # init params
        config_file = os.path.abspath('../stimprogram/psychopy/config.ini')
        self.gui_params, self.stim_params, config_dict = self.read_config_file(
            config_file)
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
        stim_config_dict = {}

        # make dict of options
        for option_dict, section in zip([default_config_dict,
                                         gui_config_dict,
                                         stim_config_dict],
                                        ['Defaults', 'GUI', 'StimProgram']):

            for option in config.options(section):
                option_dict[option] = config.get(section, option)

            # cast, for proper set up of controls
            for key, value in option_dict.iteritems():
                option_dict[key] = Parameters.lit_eval(value)

        return gui_config_dict, stim_config_dict, default_config_dict

    @staticmethod
    def lit_eval(value):
        """
        Helper method to attempt to cast parameters from strings to proper
        int/float/bool/list. Uses ast.literal_eval(), see relevant
        documentation.

        :param value: variable being casted, passed from ini file or gui so
         always string. Skip if already string
        :return: casted or unchanged variable
        """
        try:
            value = literal_eval(value)
        except (SyntaxError, ValueError):  # for strings
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

    def get_global_params(self):
        """
        Getter.

        :return: dictionary of default values from global defaults
        """
        global_dict = {}

        for param in self.global_default_param.keys():
            global_dict[param] = self.global_default_param[param]['default']

        return global_dict

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
        :param index: if a list value param, where in the list
        """
        trans = self.trans(category)

        value = Parameters.lit_eval(value)

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
        :param index: if a list value param, where in the list
        :return: the currently set parameter value
        """
        trans = self.trans(category)

        if index is None:
            return trans[param]['default']
        else:
            return trans[param]['default'][index]

    def init_params(self, config_dict):
        """
        Initializes dictionaries of parameters from json

        :param config_dict: dictionary of defaults
        """
        json_path = os.path.abspath('../stimprogram/psychopy/params_json.txt')
        with open(json_path, 'r') as f:
            params = json.load(f, object_pairs_hook=OrderedDict)

        # set defaults
        for category in params.itervalues():
            for k, param in category.iteritems():
                param['default'] = config_dict[k]

        self.shape_param = params['shape_param']
        self.timing_param = params['timing_param']
        self.fill_param = params['fill_param']
        self.motion_param = params['motion_param']
        self.global_default_param = params['global_default_param']


class TextCtrlTag(wx.TextCtrl):
    """
    Simple subclass of wx.TextCtrl for assigning ID tag to class to keep
    track of which parameter it was assigned to. Also has method to set value.
    """
    def __init__(self, *args, **kwargs):
        # pop out tag and tag2 if present from args/kwargs
        self.tag = kwargs.pop('tag', None)
        # tag2 used in list type parameters
        self.tag2 = kwargs.pop('tag2', None)
        wx.TextCtrl.__init__(self,
                             *args,
                             validator=TextCtrlValidator(),
                             **kwargs)

    def set_value(self, value):
        """
        Method to change the value in the control.

        :param value: value to be changed to
        """
        self.SetValue(str(value))

    def set_editable(self, toggle, value=None):
        """
        Toggles whether or not control is editable.

        :param toggle: True or False, whether control is editable.
        :param value: When making editable, what to set value to.
        """
        if not toggle:
            self.ChangeValue('table')
            self.SetEditable(False)

        if toggle:
            self.set_value(value)
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
        # print 'set choice'
        self.SetStringSelection(str(value))
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId,
                              self.Id)
        evt.SetEventObject(self)
        evt.SetString(str(value))
        self.GetParent().GetEventHandler().ProcessEvent(evt)

    def set_editable(self, toggle, value=None):
        """
        Toggles whether or not control is editable.
        """
        if not toggle:
            self.Append('table')
            self.SetStringSelection('table')

        if toggle:
            self.Delete(self.GetCount() - 1)
            self.set_value(value)


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
        wx.FilePickerCtrl.__init__(self, *args,
                                   message='Path to file',
                                   style=wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL,
                                   **kwargs)

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
        Normal init.
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
    of GlobalPanel.

    :param params: dictionary of parameters
    :param parent: parent window of panel (notebook)
    :param category: category of parameters
    """
    def __init__(self, params, parent, category):
        """
        Constructor
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
        self.create_inputs()

        # nest and place sizers
        panel_sizer = wx.BoxSizer()
        panel_sizer.Add(self.grid_sizer,
                        proportion=1,
                        flag=wx.ALL | wx.EXPAND,
                        border=10)

        # set sizer for panel
        self.SetSizer(panel_sizer)

    def create_inputs(self):
        """
        Method to recursively generate label and input widgets.
        Checks if param is child of another and only generates
        parent params, then generates subpanel with associated child
        params. Differentiates between input types (text, dropdown,
        list (i.e. multiple text fields)).
        """

        # iterate through params in param dict
        for param, param_info in self.params.iteritems():
            # only generate fields for params that aren't children
            if not param_info['is_child'] and 'hide' not in param_info:
                # label widget
                label = wx.StaticText(self, label=param_info['label'] + ':')

                param_type = param_info['type']

                # input widgets, depending on type
                if param_type in ['text', 'choice', 'path']:
                    ctrl = self.make_ctrls(param, param_info)

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
                    for i in range(length):
                        size = ((120 / length - (5 * (length - 1)) / length), -1)
                        ctrl = self.make_ctrls(param,
                                               param_info,
                                               tag2=i,
                                               size=size)
                        # add to sizer
                        list_sizer.Add(ctrl)

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

                # single box sizer so that subpanels can occupy a single
                # space in the panel's gridbox sizer
                subpanel_sizer = wx.BoxSizer(wx.VERTICAL)

                # iterate through the dictionary of child params
                for choice, child_params in param_info['children'].iteritems():
                    # create new ordered dict to hold only child params
                    child_param_dict = OrderedDict()

                    # iterate through list of child params and create copy of
                    # dict entry found in param dict. Need to make copy or
                    # else changes will make changes in wrong dict
                    for child_param in child_params:
                        child_param_dict[child_param] = deepcopy(
                            self.params[child_param])

                    # iterate through new child param dict and reset is_child
                    for values in child_param_dict.itervalues():
                        values['is_child'] = False

                    # make sub panel with new dict
                    self.sub_panel_dict[param][choice] = InputPanel(
                        child_param_dict, self, self.category)

                # add panels to subpanel sizer
                for panel in self.sub_panel_dict[param].itervalues():
                    subpanel_sizer.Add(panel, proportion=1, flag=wx.EXPAND)

                # add subpanel sizer to panel sizer, spanning both columns
                self.grid_sizer.Add(subpanel_sizer,
                                    pos=(self.grid_counter, 0),
                                    span=(1, 2),
                                    flag=wx.EXPAND)

                # increment grid counter
                self.grid_counter += 1

    def make_ctrls(self, tag, param_info, **kwargs):
        """
        Makes controls for create_inputs().

        :param type:
        :param tag:
        :param kwargs:
        :return: proper control
        """
        param_type = param_info['type']

        # make control
        if param_type == 'text':
            ctrl = TextCtrlTag(self,
                               size=(120, -1),
                               tag=tag,
                               value=str(param_info['default']))

        elif param_type == 'choice':
            ctrl = ChoiceCtrlTag(self,
                                 tag=tag,
                                 choices=param_info['choices'])

            # on win32, choice still displays as blank, so manually set
            # selection to default for aesthetic reasons
            ctrl.SetStringSelection(str(param_info['default']))

        elif param_type == 'path':
            ctrl = FilePickerCtrlTag(self,
                                     tag=tag,
                                     category=self.category)

        elif param_type == 'list':
            i = kwargs['tag2']
            ctrl = TextCtrlTag(self,
                               size=kwargs['size'],
                               tag=tag,
                               tag2=i,
                               value=str(param_info['default'][i]))

            tag = tag + '[' + str(i) + ']'

        # add control to dict of all controls
        if tag in self.all_controls.keys():
            # append because duplicates of some controls
            self.all_controls[tag].append(ctrl)
        else:
            self.all_controls[tag] = [ctrl]

        # bind events to proper methods
        binders = {'text'  : wx.EVT_TEXT,
                   'choice': wx.EVT_CHOICE,
                   'path'  : wx.EVT_FILEPICKER_CHANGED,
                   'list'  : wx.EVT_TEXT}

        self.Bind(binders[param_type], self.input_update, ctrl)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click, ctrl)

        return ctrl

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
        # else get the new value from the widget
        else:
            value = event.GetString()

        # if choice in grid, leave choice as table and don't do anything
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
            self.Layout()
            self.Refresh()

        # some params need to edit global defaults of StimProgram on the fly
        # instead of at window instantiation
        global_params = self.parameters.get_global_params()

        if param in ['log', 'protocol_reps', 'pref_dir', 'capture']:
            StimProgram.GlobalDefaults[param] = global_params[param]

        elif param == 'trigger_wait':
            StimProgram.GlobalDefaults['trigger_wait'] = \
                int(global_params['trigger_wait'] * 1.0 * global_params[
                    'frame_rate'] + 0.99)

        elif param == 'background':
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

    :param params: dictionary of parameters
    :param parent: parent window of panel (notebook)
    :param category: category of parameters
    """
    def __init__(self, parent, params, category):
        # super initiation
        super(GlobalPanel, self).__init__(parent, params, category)

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
        self.globals_file = os.path.abspath(os.path.join(
            self.frame.gui_params['data_dir'], 'global_defaults_new.txt'))

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
        data_folder = os.path.abspath(self.frame.gui_params['data_dir'])

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

        for param, controls in self.frame.all_controls.iteritems():
            for control in controls:
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
        self.stims_to_run_w_grid = []

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
        self.update_button = wx.Button(self, label='Update')

        self.add_button.SetMinSize((55, 26))
        self.remove_button.SetMinSize((55, 26))
        self.update_button.SetMinSize((55, 26))

        # sizer for add and remove buttons
        add_remove_update_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add buttons to sizer
        add_remove_update_sizer.Add(self.add_button,
                             proportion=1,
                             flag=wx.LEFT | wx.RIGHT,
                             border=5)

        add_remove_update_sizer.Add(self.remove_button,
                             proportion=1,
                             flag=wx.LEFT | wx.RIGHT,
                             border=5)

        add_remove_update_sizer.Add(self.update_button,
                             proportion=1,
                             flag=wx.LEFT | wx.RIGHT,
                             border=5)

        # add up down sizer to panel sizer
        panel_sizer.Add(add_remove_update_sizer,
                        proportion=0,
                        flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL |
                             wx.ALIGN_CENTER_VERTICAL,
                        border=5)

        # button binders
        self.Bind(wx.EVT_BUTTON, self.on_up_button, self.up_button)
        self.Bind(wx.EVT_BUTTON, self.on_down_button, self.down_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_button, self.add_button)
        self.Bind(wx.EVT_BUTTON, self.on_remove_button, self.remove_button)
        self.Bind(wx.EVT_BUTTON, self.on_update_button, self.update_button)

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

        class_names = ['StaticStim',
                       'MovingStim',
                       'RandomlyMovingStim',
                       'TableStim',
                       'ImageJumpStim']

        label_names = ['static',
                       'moving',
                       'random',
                       'table',
                       'jump']

        if stim_type in class_names:
            return label_names[class_names.index(stim_type)]

        elif stim_type in label_names:
            return class_names[label_names.index(stim_type)]

        else:
            raise AttributeError('Wrong label or stim class')

    def on_add_button(self, event, insert_pos=None):
        """
        Makes call to add to list with proper params

        :param event:
        :param insert_pos:
        """
        param_dict = self.parameters.get_merged_params()
        stim_type = param_dict.pop('move_type')
        grid_dict = self.frame.grid.get_grid_dict()

        self.add_to_list(stim_type, param_dict, grid_dict, insert_pos)

    def add_to_list(self, stim_type, param_dict, grid_dict, insert_pos=None):
        """
        Adds stim to list of stims to run, as a bew stiminfo class

        :param stim_type:
        :param param_dict:
        :param grid_dict:
        :param insert_pos: at which position in list to insert stim. Used
         when moving stims up and down
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

        # stim info instance to store and grid control_dict instance to store
        stim_info = StimProgram.StimInfo(stim_type, param_dict, insert_pos)

        # add to list of stims to run along with grid info
        if insert_pos is not None:
            self.stims_to_run.insert(insert_pos, stim_info)
            self.stims_to_run_w_grid.insert(insert_pos, grid_dict)
        else:
            self.stims_to_run.append(stim_info)
            self.stims_to_run_w_grid.append(grid_dict)

        # deselect all in list and select most recently added
        while self.list_control.GetSelectedItemCount() != 0:
            self.list_control.Select(self.list_control.GetFirstSelected(),
                                     on=0)
        self.list_control.Select(insert_pos)

        # print self.stims_to_run_w_grid

    def on_remove_button(self, event, clear_all=False):
        """
        Removes stims from stim list. If none selected, clears all.

        :param event:
        """
        # if any selected, iterate through and delete
        if self.list_control.GetSelectedItemCount() > 0 and not clear_all:
            for i in range(self.list_control.GetSelectedItemCount()):
                selected = self.list_control.GetFirstSelected()
                # remove from stims to run
                del self.stims_to_run[selected]
                del self.stims_to_run_w_grid[selected]
                # remove from list
                self.list_control.DeleteItem(selected)

            # reset stim numbers in stims to run
            for i, stim in enumerate(self.stims_to_run):
                stim.number = i

        else:
            self.list_control.DeleteAllItems()
            # clear stims to run
            del self.stims_to_run[:]
            del self.stims_to_run_w_grid[:]

    def on_update_button(self, event):
        """
        Removes stims and adds stim to list, in essence updating/refreshing
        the currently selected stim.

        :param event:
        """
        # if any selected, iterate through and delete
        if self.list_control.GetSelectedItemCount() == 1:
            index = self.list_control.GetFirstSelected()
            self.on_remove_button(event)
            self.on_add_button(event, index)

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

                # get grid dict
                grid_dict = self.stims_to_run_w_grid[index]

                # remove
                self.on_remove_button(event)

                # re-add
                self.add_to_list(stim_type, param_dict, grid_dict, index - 1)

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

                # get grid dict
                grid_dict = self.stims_to_run_w_grid[index]

                # remove
                self.on_remove_button(event)

                # readd
                self.add_to_list(stim_type, param_dict, grid_dict, index + 1)

                # reset stim numbers in stims to run
                for i, stim in enumerate(self.stims_to_run):
                    stim.number = i

    def on_double_click(self, event):
        """
        Loads params from list and for grid on double click

        :param event:
        """
        selected = self.list_control.GetFirstSelected()
        stim = self.stims_to_run[selected]
        grid_dict = self.stims_to_run_w_grid[selected]
        # copy so adding move type doesn't affect StimInfo instance
        params = deepcopy(stim.parameters)

        stim_type = self.convert_stim_type(stim.stim_type)
        params['move_type'] = stim_type

        # compatibility for old checkerboards
        if 'check_type' not in params.iterkeys():
            if params['fill_mode'] == 'random':
                params['fill_mode'] = 'checkerboard'
                params['check_type'] = 'random'
            elif params['fill_mode'] == 'checkerboard':
                params['check_type'] = 'checkerboard'

        grid = self.frame.grid

        # post events to grid to simulate removing columns to clear text and
        # make controls editable again
        for col in range(grid.grid.GetNumberCols()):
            evt = wx.grid.GridEvent(grid.grid.GetId(),
                                    wx.grid.wxEVT_GRID_LABEL_RIGHT_CLICK,
                                    grid,
                                    row=-1,
                                    col=0)
            grid.GetEventHandler().ProcessEvent(evt)

        # iterate through params and set values
        for param, controls in self.frame.all_controls.iteritems():
            for control in controls:
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

        # iterate through values in grid dict and populate
        col_index = 0
        for param, values in grid_dict.iteritems():
            # simulate adding param to grid
            ctrl = self.frame.all_controls[param][0]
            evt = wx.CommandEvent(wx.EVT_CONTEXT_MENU.typeId,
                                  ctrl.Id)
            evt.SetEventObject(ctrl)
            ctrl.GetParent().GetEventHandler().ProcessEvent(evt)

            # iterate through values and populate column and grid control_dict
            for i, value in enumerate(values):
                if value is not None:
                    try:
                        grid.grid.SetCellValue(i, col_index, str(values[i]))
                        grid.control_dict[param][i] = values[i]
                    # if out of rows, add more
                    except wx._core.PyAssertionError:
                        # send add more rows event
                        evt = wx.grid.GridEvent(grid.grid.GetId(),
                                                wx.grid.wxEVT_GRID_LABEL_RIGHT_CLICK,
                                                grid,
                                                row=-1,
                                                col=-1)
                        grid.GetEventHandler().ProcessEvent(evt)
                        # retry adding
                        grid.grid.SetCellValue(i, col_index, str(values[i]))
                        grid.control_dict[param][i] = values[i]

            col_index += 1

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
        default_dir = os.path.abspath(self.frame.gui_params['saved_stim_dir'])
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
            # add grid dict in to parameters
            params['grid_dict'] = self.frame.list_panel.stims_to_run_w_grid[i]
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

        is_log = 'logs' in path

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
            # take back out grid dict
            try:
                grid_dict = params.pop('grid_dict')
            except KeyError:
                try:
                    grid_dict = params.pop('control_list')
                except KeyError:
                    grid_dict = {}

            # compatibility for old checkerboards
            if 'check_type' not in params.iterkeys():
                if params['fill_mode'] == 'random':
                    params['fill_mode'] = 'checkerboard'
                    params['check_type'] = 'random'
                elif params['fill_mode'] == 'checkerboard':
                    params['check_type'] = 'checkerboard'

            # convert from StimProgram instance label to stim type
            stim_type = self.frame.list_panel.convert_stim_type(stim_type)

            # load
            self.frame.list_panel.add_to_list(stim_type, params, grid_dict)

        print '\nStim(s) loaded'

    def on_double_click(self, event):
        """
        If log file, opens, else loads.

        :param event:
        """
        path = self.browser.GetPath()

        is_log = os.path.split(os.path.split(os.path.dirname(path))[0])[1] ==\
            'logs'

        if is_log:
            if platform == 'win32':
                os.startfile(path)
            elif platform == 'darwin':
                os.system('open ' + path)

        else:
            if wx.GetMouseState().ControlDown():
                self.on_load_button(event)
            else:
                self.frame.list_panel.on_remove_button(event, clear_all=True)
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
        ctrls = self.frame.all_controls[param]

        if param not in self.control_dict and ctrls[0].GetParent().category \
                != 'global':
            # add column to grid
            self.grid.ClearSelection()
            self.grid.AppendCols(1)
            self.grid.SetGridCursor(0, self.grid.GetNumberCols() - 1)
            self.grid.SetColLabelValue(self.grid.GetNumberCols() - 1, param)

            # get value of control
            try:
                value = self.parameters.get_param_value(
                    ctrls[0].GetParent().category, param)
            except:
                index = int(param[-2])
                value = self.parameters.get_param_value(
                    ctrls[0].GetParent().category, param[:-3], index)

            value = str(value)

            # if no other rows, add some, and populate control dict
            if self.grid.NumberCols == 1:
                self.grid.AppendRows(5)
                self.control_dict[param] = [None] * 5
            else:
                self.control_dict[param] = [None] * (self.grid.GetNumberRows())

            self.control_dict[param][0] = value

            for ctrl in ctrls:
                ctrl.set_editable(False)

            self.grid.SetCellValue(0, self.grid.GetNumberCols() - 1, value)

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
                for ctrl in self.frame.all_controls[param]:
                    ctrl.set_editable(True, value=old_value)

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

        self.grid.SetCellValue(row, col, '')
        self.control_dict[param][row] = None

    def get_grid_dict(self):
        """
        Getter. Sets middle Nones to previous values.

        :return: edited dictionary of params and values in grid
        """
        to_return = {}
        to_edit = deepcopy(self.control_dict)

        for param, values in to_edit.iteritems():
            if values[0] is None:
                raise IndexError('First value of table cannot be empty.')

            # get number of terminal Nones
            for i, value in reversed(list(enumerate(values))):
                if value is None:
                    pass
                else:
                    where_stop = i
                    break

            # iterate until terminal nones
            for i in range(0, where_stop):
                if values[i] is None:
                    values[i] = values[i - 1]

            values = map(Parameters.lit_eval, values)
            to_return[param] = values

        return to_return


class MyMenuBar(wx.MenuBar):
    """
    Class for custom menu bar.
    """
    def __init__(self, parent):
        """
        Constructor.
        """
        super(MyMenuBar, self).__init__()

        self.frame = parent

        # menus
        file_menu = wx.Menu()
        view_menu = wx.Menu()
        options_menu = wx.Menu()

        # file menus
        file_quit = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')

        # view menus
        view_logs = view_menu.Append(wx.ID_ANY, 'logs', 'Open log folder')
        view_stims = view_menu.Append(wx.ID_ANY, 'stims', 'Open stim folder')

        # options menus
        self.options_log = options_menu.Append(wx.ID_ANY, 'log',
                                               'Save runs to log file',
                                               kind=wx.ITEM_CHECK)
        self.options_log.Toggle()  # default to True
        self.options_capture = options_menu.Append(wx.ID_ANY, 'capture',
                                                   'Capture run and create '
                                                   'video',
                                                   kind=wx.ITEM_CHECK)
        self.options_mirror = options_menu.Append(wx.ID_ANY, 'mirror',
                                                   'Make small mirror window',
                                                   kind=wx.ITEM_CHECK)
        # options submenu
        options_tools = wx.Menu()
        tools_rec_map = options_tools.Append(wx.ID_ANY,
                                             'Map receptive field',
                                             'Generate receptive field map')
        options_menu.AppendMenu(wx.ID_ANY, 'Tools', options_tools)

        # add top level menus to menu bar
        self.Append(file_menu, '&File')
        self.Append(view_menu, '&View')
        self.Append(options_menu, '&Options')

        self.Bind(wx.EVT_MENU, self.on_file_quit, file_quit)
        self.Bind(wx.EVT_MENU, self.on_view_logs, view_logs)
        self.Bind(wx.EVT_MENU, self.on_view_stims, view_stims)
        self.Bind(wx.EVT_MENU, self.on_options_log, self.options_log)
        self.Bind(wx.EVT_MENU, self.on_options_capture, self.options_capture)
        self.Bind(wx.EVT_MENU, self.on_options_mirror, self.options_mirror)
        self.Bind(wx.EVT_MENU, self.on_options_tools_rec_map, tools_rec_map)

    def on_file_quit(self, event):
        """
        Handles quitting.
        """
        self.frame.Close()

    def on_view_logs(self, event):
        """
        Handles request to view logs
        """
        logs_dir = self.frame.stim_params['logs_dir']

        if platform == "win32":
            os.startfile(logs_dir)
        elif platform == "darwin":
            subprocess.Popen(["open", logs_dir])

    def on_view_stims(self, event):
        """
        Handles request to view stims
        """
        stim_dir = self.frame.gui_params['saved_stim_dir']

        if platform == "win32":
            os.startfile(stim_dir)
        elif platform == "darwin":
            subprocess.Popen(["open", stim_dir])

    def on_options_log(self, event):
        """
        Handles toggling logging

        :param event:
        :return:
        """
        val = self.options_log.IsChecked()

        self.frame.parameters.set_param_value('global', 'log', val)
        StimProgram.GlobalDefaults['log'] = val

    def on_options_capture(self, event):
        """
        Handles toggling capturing

        :param event:
        :return:
        """
        val = self.options_capture.IsChecked()

        self.frame.parameters.set_param_value('global', 'capture', val)
        StimProgram.GlobalDefaults['capture'] = val

    def on_options_mirror(self, event):
        """
        Handles toggling capturing

        :param event:
        :return:
        """
        val = self.options_mirror.IsChecked()

        self.frame.parameters.set_param_value('global', 'small_win', val)
        StimProgram.GlobalDefaults['small_win'] = val

    def on_options_tools_rec_map(self, event):
        """
        Handles request to map receptive field_rect

        :param event:
        :return:
        """
        # start dialog to select folders
        log_dir = os.path.abspath(self.frame.stim_params['logs_dir'])
        prompt = 'Select folder(s) with desired JumpStim logs'
        folder_select_dialog = mdd.MultiDirDialog(self.frame,
                                                  message=prompt,
                                                  defaultPath=log_dir,
                                                  agwStyle=mdd.DD_MULTIPLE)

        # to exit out of dialog on cancel
        if folder_select_dialog.ShowModal() == wx.ID_CANCEL:
            return

        jump_paths = folder_select_dialog.GetPaths()

        # GetPaths of MultiDirDialog prepends volume information to paths,
        # so need to strip out, platform dependant
        if platform == 'win32':
            jump_paths = map(lambda x: x.split()[2].replace(')',
                             '').replace('(', ''), jump_paths)
            jump_paths = map(os.path.abspath, jump_paths)
        elif platform == 'darwin':
            jump_paths = map(lambda x: x.replace('Macintosh HD', ''),
                             jump_paths)

        try:
            for jump in jump_paths:
                assert os.path.exists(jump)
        except AssertionError:
            print '\nOne or more of the selected paths do not exist:'
            for jump in jump_paths:
                print '    {}'.format(jump)
            return

        prompt = 'Select heka wave file'

        wave_dialog = wx.FileDialog(self.frame,
                                    message=prompt,
                                    # defaultDir=default_dir,
                                    wildcard='*.dat',
                                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        # to exit out of dialog on cancel button
        if wave_dialog.ShowModal() == wx.ID_CANCEL:
            return

        wave_path = os.path.abspath(wave_dialog.GetPath())

        wave_details = self.prompt_wave_details()

        kwargs = dict(dat_file=wave_path,
                      jump_logs=jump_paths,
                      group=int(wave_details['group']),
                      series=int(wave_details['series']),
                      sweep=map(int, wave_details['sweep'].replace(' ',
                          '').split(',')),
                      data_trace=int(wave_details['data_trace']),
                      trigger_trace=int(wave_details['trigger_trace']),
                      thresh=wave_details['thresh'],
                      center_on=wave_details['center_on'],
                      window=float(wave_details['window']),
                      latency=int(wave_details['latency']),
                      num_frames=int(wave_details['num_frames'])
                      )

        # for k, v in kwargs.iteritems():
        #     print k, v

        try:
            from heka_reader import process_data
            rec_field = process_data.main(**kwargs)
        except Exception as e:
            print traceback.print_exc()
            print 'Something went wrong: {}'.format(e)
            return

        rec_field = Image.fromarray(rec_field)
        rec_field.show()

        # default_dir = os.path.abspath('./psychopy/stims/')

        # popup save dialog
        save_dialog = wx.FileDialog(self.frame,
                                    message='Save receptive field map?',
                                    wildcard='.png',
                                    # defaultDir=default_dir,
                                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        # to exit out of popup on cancel button
        if save_dialog.ShowModal() == wx.ID_CANCEL:
            return

        path = save_dialog.GetPath()
        print path

        rec_field.save(path)
        return

    def prompt_wave_details(self):
        """
        Dialog to prompt for details about the heka file.
        """
        params = OrderedDict([
            ('group',
             {'label': 'group',
              'default': ''}
             ),

            ('series',
             {'label': 'series',
              'default': ''}
             ),

            ('sweep',
             {'label': 'sweeps (csv)',
              'default': ''}
             ),

            ('data_trace',
             {'label': 'data trace',
              'default': '1'}
             ),

            ('trigger_trace',
             {'label': 'trigger trace',
              'default': '3'}
             ),

            ('thresh',
             {'label': 'threshold',
              'default': '2'}
             ),

            ('center_on',
             {'label' : 'center on (min, max)',
              'default': 'min'}
             ),

            ('window',
             {'label': 'spike width (ms)',
              'default': '0.75'}
             ),

            ('latency',
             {'label': 'latency (ms)',
              'default': '10'}
             ),

            ('num_frames',
             {'label': 'prev. frames to avg',
              'default': '3'}
             ),
            ])

        dlg = wx.Dialog(parent=None, title='Wave details')

        # inputs sizer
        inputs_sizer = wx.FlexGridSizer(rows=len(params), cols=2, vgap=5,
                                        hgap=5)

        inputs = []

        for tag, values in params.iteritems():
            label = wx.StaticText(dlg, label=values['label'] + ':')
            ctrl = TextCtrlTag(dlg,
                               size=(-1, -1),
                               tag=tag,
                               value=values['default'])

            inputs.append(ctrl)

            inputs_sizer.Add(label)
            inputs_sizer.Add(ctrl)

        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(inputs_sizer,
                      proportion=0,
                      flag=wx.EXPAND | wx.TOP | wx.LEFT,
                      border=5)

        button_sizer = dlg.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        dlg_sizer.Add(button_sizer,
                      proportion=0,
                      flag=wx.EXPAND | wx.TOP | wx.BOTTOM,
                      border=10)

        dlg.SetSizer(dlg_sizer)
        dlg_sizer.Fit(dlg)

        # to exit out of dialog on cancel button
        if dlg.ShowModal() == wx.ID_CANCEL:
            return

        dlg.Destroy()

        ret = {}

        for input in inputs:
            ret[input.tag] = input.GetValue()

        return ret


class MyStatusBar(wx.StatusBar):
    """
    Class for custom status bar to color background on errors.
    """
    def __init__(self, parent):
        super(MyStatusBar, self).__init__(parent, 1)

        self.SetFieldsCount(1)
        self.text_box = wx.StaticText(self, -1, ' hello')

        # size is weird on win32, so adjust for aesthetics
        if platform == 'win32':
            field_rect = self.GetFieldRect(0)
            field_rect.y += 3
            self.text_box.SetRect(field_rect)

    def set_status_text(self, text):
        self.text_box.SetLabel(text)

    def set_background(self, color):
        self.text_box.SetBackgroundColour(color)

    def set_text_color(self, color):
        self.text_box.SetForegroundColour(color)


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
        self.gui_params = self.parameters.gui_params
        self.stim_params = self.parameters.stim_params

        # instance attributes
        self.win_open = False
        self.all_controls = {}
        self.do_break = False

        # make grid
        self.grid = MyGrid(self)

        # notebook to hold input panels
        self.input_nb = wx.Notebook(self)

        # instantiate panels with notebook as parent
        notebook_info = [[self.parameters.shape_param,
                          self.parameters.timing_param,
                          self.parameters.fill_param,
                          self.parameters.motion_param],
                         ['shape', 'timing', 'fill', 'motion']]

        pages = [InputPanel(params, self.input_nb, name) for params, name in
                 zip(*notebook_info)]

        for page, name in zip(pages, ['Shape', 'Time', 'Fill', 'Motion']):
            self.input_nb.AddPage(page, name)

        # instantiate global panel
        self.panel_global = GlobalPanel(self.parameters.global_default_param,
                                        self, 'global')

        # sizer to hold notebook and global panel
        panel_row = wx.BoxSizer(wx.HORIZONTAL)

        # add notebook panel and global panel to sizer
        panel_row.Add(self.input_nb, proportion=1, flag=wx.EXPAND)
        panel_row.Add(self.panel_global, proportion=1, flag=wx.EXPAND)

        # create buttons
        button_labels = ['Run', 'Stop', 'Window', 'Exit']
        buttons = [wx.Button(self, label=label) for label in button_labels]

        button_callback = [self.on_run_button,
                           self.on_stop_button,
                           self.on_win_button,
                           self.on_exit_button]

        # sizer for buttons under panel_row
        stim_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # set binders and add to sizer
        for button, button_func in zip(buttons, button_callback):
            self.Bind(wx.EVT_BUTTON, button_func, button)
            stim_buttons_sizer.Add(button,
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
        self.status_bar = MyStatusBar(self)
        self.SetStatusBar(self.status_bar)

        # menu bar
        self.menu_bar = MyMenuBar(self)
        self.SetMenuBar(self.menu_bar)

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

        # location
        self.SetPosition(self.gui_params['window_pos'])

        # draw frame
        self.Show()

    def on_run_button(self, event):
        """
        Method for calling run and changing values from grid if necessary.

        :param event:
        """
        if len(self.list_panel.stims_to_run) != 0:
            if self.win_open:
                self.on_stop_button(event)
                self.do_break = False

                # get length of longest list in grid
                grid_max = 0

                for stim in self.list_panel.stims_to_run_w_grid:
                    if stim:
                        for values in stim.itervalues():
                            length = sum(x is not None for x in values)
                            grid_max = max(grid_max, length)

                if grid_max == 0:
                    self.run()

                else:
                    # run through grid
                    for i in range(grid_max):

                        # for each stim to be run
                        for j, stim in \
                                enumerate(self.list_panel.stims_to_run_w_grid):

                            # for each grid dict
                            for param, values in stim.iteritems():

                                # set values
                                value = values[i]
                                if value is not None:

                                    try:
                                        # list types
                                        if param[-1] == ']':
                                            index = int(param[-2])
                                            fixed_param = param[:-3]

                                            # change parameter
                                            self.list_panel.stims_to_run[
                                                j].parameters[
                                                fixed_param][index] = value

                                        # convert to instances
                                        elif param == 'move_type':
                                            value = \
                                                self.list_panel.\
                                                convert_stim_type(value)

                                            self.list_panel.stims_to_run[
                                                j].stim_type = value

                                        else:
                                            self.list_panel.stims_to_run[
                                                j].parameters[param] = value

                                    # if reach end of some lists
                                    except IndexError:
                                        pass

                        if self.do_break:
                            break

                        self.run()

            else:
                self.on_win_button(event)
                self.on_run_button(event)

        else:
            print 'Please add stims.'
            self.SetStatusText('Please add stims.')

    def run(self):
        """
        Method for running stims.
        """
        # try/except, so that uncaught errors thrown by StimProgram can be
        # caught to avoid hanging.
        try:
            self.status_bar.set_background(wx.NullColour)
            self.status_bar.set_text_color(wx.BLACK)
            self.status_bar.set_status_text('running...')
            fps, time, time_stamp = StimProgram.main(
                self.list_panel.stims_to_run)

            if time != 'error':
                status_text = 'Last run: {0:.2f} fps, '.format(fps) \
                              + '{0:.2f} seconds.'.format(time)

                if time_stamp is not None:
                    status_text += ' Timestamp: {}'.format(time_stamp)

                self.status_bar.set_status_text(status_text)
            # if error
            else:
                self.status_bar.set_status_text('Error: {}'.format(fps))
                self.status_bar.set_background(wx.BLUE)
                self.status_bar.set_text_color(wx.WHITE)

        except:
            raise

    def on_win_button(self, event):
        """
        Method for toggling stim window. Makes call to StimProgram. Gets
        various params from global panel.

        :param event: event passed by binder
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
