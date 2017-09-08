# NEED MUCH MORE COVERAGE
from pyStim import pyStim
# import unittest
# import mock
import numpy as np
# import u3
import pytest


# class TestTrigger(unittest.TestCase):
#
    # @mock.path.object(StimProgram.MyWindow, 'make_win')
    # @mock.patch('u3.U3')
    # def test_send_trigger(self, mock_U3):
    #     StimProgram.has_u3 = True
    #
    #     reference = StimProgram.MyWindow()
    #     reference.d = u3.U3()
    #     print reference.d
    #     reference.send_trigger()
    #
    #     self.assertTrue(mock_U3.called)


class TestGenRGB(object):

    # deltas are weird because they're absolute differences, so to make sense
    # think in terms of the scaling back to 0, 1 interval

    def test_bg0_mode_rgb_channel_all_color_1(self):
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

    def test_uniform_channell_all_color_1(self):
        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)
        tex = stim.gen_texture()
        print tex

        np.testing.assert_array_equal(tex,
                                      np.array([[[1.0, 1.0, 1.0, 1.0]]]))

    def test_uniform_channell_all_color_05(self):
        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='all',
                                 color_mode='rgb',
                                 color=[0.5, 0.5, 0.5],
                                 alpha=0.5)
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[0.5, 0.5, 0.5, 0.5]]]))

    def test_uniform_channell_green_color_1(self):
        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='green',
                                 color_mode='rgb',
                                 color=[1, 1, 1],
                                 alpha=1)
        tex = stim.gen_texture()
        print tex

        np.testing.assert_array_equal(tex,
                                      np.array([[[-1.0, 1.0, -1.0, 1.0]]]))

    def test_uniform_channell_green_color_05(self):
        stim = pyStim.StaticStim(fill_mode='uniform',
                                 size=[4, 4],
                                 contrast_channel='green',
                                 color_mode='rgb',
                                 color=[0.5, 0.5, 0.5],
                                 alpha=0.5)
        tex = stim.gen_texture()

        np.testing.assert_array_equal(tex,
                                      np.array([[[-1.0, 0.5, -1.0, 0.5]]]))