"""
Tests for pystim.
"""

import os
import sys

sys.path.append(os.path.abspath('pyStim'))

import pickle

import numpy as np
import psychopy
import pytest
from mock import Mock, patch

import pyStim

try:
    import u3
    HAS_U3 = True
except ImportError:
    HAS_U3 = False

class TestDrawTimes(object):

    # TODO: test triggering

    def test_draw_times_no_force_stop_no_trigger(self):
        pyStim.GlobalDefaults['frame_rate'] = 100

        stim = pyStim.StaticStim(delay=1,
                                 duration=2,
                                 end_delay=1,
                                 force_stop=0,
                                 trigger=False)
        duration = stim.draw_times()

        assert stim.start_stim == 100
        assert stim.end_stim == 300
        assert stim.end_delay == 100
        assert stim.force_stop == 0
        assert stim.draw_duration == 200

        assert duration == 400

    def test_draw_times_force_stop_no_trigger(self):
        pyStim.GlobalDefaults['frame_rate'] = 100

        stim = pyStim.StaticStim(delay=1,
                                 duration=2,
                                 end_delay=1,
                                 force_stop=2,
                                 trigger=False)
        duration = stim.draw_times()

        assert stim.start_stim == 100
        assert stim.end_stim == 200
        assert stim.end_delay == 0
        assert stim.force_stop == 200
        assert stim.draw_duration == 200

        assert duration == 200


class TestGenRGB(object):

    # deltas are weird because they're absolute differences, so to make sense
    # of think in terms of the scaling back to 0, 1 interval

    def test_bg0_mode_rgb_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([1.0, 1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([-1.0, -1.0, -1.0, 1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([0., 0., 0.]))
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_rgb_channel_all_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='rgb',
                                 color=[0.5, -0.5, 0.5],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([0.5, -0.5, 0.5, 1]))
        np.testing.assert_array_equal(low,
                                      np.array([-0.5, 0.5, -0.5, 1]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -1.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_rgb_channel_green_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 1.0
        assert low == -1.0
        assert delta == 0.0
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_rgb_channel_green_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='rgb',
                                 color=[0.5, 0.5, 0.5],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 0.5
        assert low == -0.5
        assert delta == -0.5
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_intensity_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([1.0, 1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([-1.0, -1.0, -1.0, 1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([0., 0., 0.]))
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_intensity_channel_all_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=0.5,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([0.5, 0.5, 0.5, 1]))
        np.testing.assert_array_equal(low,
                                      np.array([-0.5, -0.5, -0.5, 1]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -0.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_intensity_channel_all_color_05_alpha_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=0.5,
                                 alpha=0.5)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([0.5, 0.5, 0.5, 0.5]))
        np.testing.assert_array_equal(low,
                                      np.array([-0.5, -0.5, -0.5, 0.5]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -0.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_intensity_channel_green_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 1.0
        assert low == -1.0
        assert delta == 0.0
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg0_mode_intensity_channel_gren_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='intensity',
                                 intensity=0.5,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 0.5
        assert low == -0.5
        assert delta == -0.5
        np.testing.assert_array_equal(background,
                                      np.array([0., 0., 0.]))

    def test_bg05_mode_rgb_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([1.0, 1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([0., 0., 0., 1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -0.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_rgb_channel_all_color_075(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='rgb',
                                 color=[0.75, -0.75, 0.75],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([0.75, -0.75, 0.75, 1]))
        np.testing.assert_array_equal(low,
                                      np.array([0.25, 1.0, 0.25, 1]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.75, -2.25, -0.75]))
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_rgb_channel_green_color_1(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 1.0
        assert low == 0.0
        assert delta == -0.5
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_rgb_channel_green_color_075(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='rgb',
                                 color=[0.75, 0.75, 0.75],
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 0.75
        assert low == 0.25
        assert delta == -0.75
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([1.0, 1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([-1.0, -1.0, -1.0, 1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -0.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_all_color_05(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=0.5,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([1.0, 1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([-0.25, -0.25, -0.25,  1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.5, -0.5, -0.5]))
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_all_color_025(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=0.25,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        np.testing.assert_array_equal(high,
                                      np.array([0.875, 0.875, 0.875, 1.0]))
        np.testing.assert_array_equal(low,
                                      np.array([0.125, 0.125, 0.125,  1.0]))
        np.testing.assert_array_equal(delta,
                                      np.array([-0.625, -0.625, -0.625]))
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_green_color_1(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 1.0
        assert low == -1.0
        assert delta == -0.5
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_gren_color_05(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='intensity',
                                 intensity=0.5,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 1.0
        assert low == -0.25
        assert delta == -0.5
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))

    def test_bg05_mode_intensity_channel_gren_color_025(self):
        pyStim.GlobalDefaults['background'] = [0.5, 0.5, 0.5]

        stim = pyStim.StaticStim(contrast_channel='green',
                                 color_mode='intensity',
                                 intensity=0.25,
                                 alpha=1)

        high, low, delta, background = stim.gen_rgb()

        assert high == 0.875
        assert low == 0.125
        assert delta == -0.625
        np.testing.assert_array_equal(background,
                                      np.array([0.5, 0.5, 0.5]))


class TestGenSize(object):

    def test_is_image(self):
        stim = pyStim.StaticStim(fill_mode='image',
                                 image_size=[100,100])
        assert stim.gen_size() == (100, 100)

    def test_is_rectangle(self):
        stim = pyStim.StaticStim(shape='rectangle',
                                 size=[100, 200])
        assert stim.gen_size() == (100, 200)
        assert stim.shape == 'rectangle'

    def test_is_circle(self):
        stim = pyStim.StaticStim(shape='circle',
                                 outer_diameter=40)
        assert stim.gen_size() == (40, 40)
        assert stim.shape == 'circle'

    def test_is_annulus(self):
        stim = pyStim.StaticStim(shape='annulus',
                                 outer_diameter=40,
                                 inner_diameter=10)
        assert stim.gen_size() == (40, 40)
        assert stim.shape == 'annulus'


class TestGenMask(object):

    def test_is_circle(self):
        stim = pyStim.StaticStim(shape='circle')
        assert stim.gen_mask() == 'circle'

    def test_is_annulus(self):
        stim = pyStim.StaticStim(shape='annulus')
        assert stim.gen_mask() == 'circle'

    def test_is_rectangle(self):
        stim = pyStim.StaticStim(shape='rectangle')
        assert stim.gen_mask() is None


class TestGenTexture(object):

    # TODO: test image texture
    # TODO: test non uniform in red channel

    def test_uniform_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)
        stim.colors = stim.gen_rgb()
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))

    def test_uniform_channell_all_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='rgb',
                                 color=[0.5, 0.5, 0.5],
                                 alpha=0.5)
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[0.5, 0.5, 0.5, 0.5]]]))

    def test_uniform_channel_green_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='green',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[-1.0, 1.0, -1.0, 1.0]]]))

    def test_uniform_channel_green_color_05(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='green',
                                 color_mode='rgb',
                                 color=[0.5, 0.5, 0.5],
                                 alpha=0.5)
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[-1.0, 0.5, -1.0, 0.5]]]))

    def test_sin_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='sine',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)
        tex = stim.gen_texture()[0, :, 0]

        np.testing.assert_array_equal(tex,
                                      np.array([0., 1.0, 0., -1.0]))

    def test_square_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='square',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)
        tex = stim.gen_texture()[0, :, 0]

        np.testing.assert_array_equal(tex,
                                      np.array([1.0, 1.0, -1.0, -1.0]))

    def test_concentric_channel_all_color_1(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='concentric',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)
        tex = stim.gen_texture()[2, :, 0]

        np.testing.assert_almost_equal(tex,
                                       np.array([0.841471, 0., -0.841471, 0.]),
                                       decimal=6)

    def test_annulus(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='annulus',
                                 outer_diameter=5,
                                 inner_diameter=2,
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 alpha=1)
        tex = stim.gen_texture()[2, :, 3]

        np.testing.assert_array_equal(tex,
                                      np.array([1.0, 1.0, -1.0, -1.0, 1.0]))


class TestGenTiming(object):

    # TODO: test at other background levels
    # TODO: test small_stim

    def test_sine_single_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_sine_both_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)

    def test_sine_single_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_sine_both_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)

    def test_sine_single_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_sine_single_negint_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=-11,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_sine_both_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sine',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_almost_equal(stim.stim.tex,
                                       np.array([[[0., 0., 0., 1.0]]]),
                                       decimal=6)

    def test_square_single_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_square_both_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))

    def test_square_single_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_square_both_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))

    def test_square_single_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_square_single_negint_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=-11,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_square_both_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='square',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(59)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))

    def test_saw_single_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_saw_both_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))

    def test_saw_single_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_saw_both_red_black(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='black',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))

    def test_saw_single_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_saw_single_negint_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=-11,
                                 intensity_dir='single',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))

    def test_saw_both_red_opposite(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='sawtooth',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))

    def test_linear_single_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 alpha=1,
                                 timing='linear',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.25, 0.25, 0.25, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.75, 0.75, 0.75, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))

    def test_linear_both_all(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 alpha=1,
                                 timing='linear',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, -1.0, -1.0, 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))

    def test_linear_single_red(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='single',
                                 alpha=1,
                                 timing='linear',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.25, -0.25, -0.25, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.75, -0.75, -0.75, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))

    def test_linear_both_red_opp(self):
        pyStim.GlobalDefaults['background'] = [0., 0., 0.]
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(fill_mode='uniform',
                                 shape='rectangle',
                                 size=[4, 4],
                                 contrast_channel='red',
                                 color_mode='intensity',
                                 intensity=1,
                                 intensity_dir='both',
                                 contrast_opp='opposite',
                                 alpha=1,
                                 timing='linear',
                                 frequency=1,
                                 duration=1)

        stim.draw_times()
        stim.stim = Mock()
        stim.stim.tex = stim.gen_texture()

        stim.gen_timing(0)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-1.0, 1.0, 1.0, 1.0]]]))
        stim.gen_timing(15)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[-0.5, 0.5, 0.5, 1.0]]]))
        stim.gen_timing(30)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0., 0., 0., 1.0]]]))
        stim.gen_timing(45)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[0.5, -0.5, -0.5, 1.0]]]))
        stim.gen_timing(60)
        np.testing.assert_array_equal(stim.stim.tex,
                                      np.array([[[1.0, -1.0, -1.0, 1.0]]]))

    def test_small_stim(self):
        stim = pyStim.StaticStim()
        stim.draw_times()

        stim.stim = Mock()
        stim.small_stim = Mock()

        stim.gen_texture()


class TestGenPhase(object):

    def test_no_phase(self):
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim()
        stim.stim = Mock()
        stim.stim.phase = np.array([0., 0.])
        stim.gen_phase()
        np.testing.assert_array_equal(stim.stim.phase,
                                      np.array([0., 0.]))

    def test_phase(self):
        pyStim.GlobalDefaults['frame_rate'] = 60

        stim = pyStim.StaticStim(phase_speed=[60, 120])
        stim.stim = Mock()
        stim.stim.phase = np.array([0., 0.])
        stim.gen_phase()
        np.testing.assert_array_equal(stim.stim.phase,
                                      np.array([1., 2.]))


@pytest.mark.xfail
class TestSetRGB(object):

    # TODO: figure out mocking here

    # @patch.object(psychopy.visual.GratingStim, 'setColor')
    def test_set_rgb(self):
        stim = pyStim.StaticStim()

        win = Mock(spec=psychopy.visual.Window)
        shape = Mock(spec=psychopy.visual.ShapeStim)
        stim.stim = shape(win)

        with patch.object(psychopy.visual.basevisual.ColorMixin, 'setColor') as mock:
            stim.set_rgb((0, 0, 0))

        assert mock.called


class TestConfigFile(object):

    def test_open_pickle_globals(self):
        g = None
        p = pyStim.config.get('GUI', 'data_dir')

        globals_file = os.path.abspath(os.path.join(p, 'global_defaults.txt'))
        if os.path.exists(globals_file):
            with open(globals_file, 'rb') as f:
                g = pickle.load(f)

            assert g is not None
        else:
            assert g is None

class TestTrigger(object):

    def test_send_ttl(self):
        if HAS_U3:
            w = pyStim.MyWindow
            try:
                w.d = u3.U3()
                w.send_trigger()
                assert True
            except AttributeError:  # on travis, can't install labjack driver
                w.d = Mock(spec=u3.U3)

                with patch.object(pyStim.MyWindow, 'send_trigger') as mock:
                    w.send_trigger()
                assert mock.called()
