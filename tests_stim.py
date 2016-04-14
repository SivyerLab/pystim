# NEED MUCH MORE COVERAGE

import StimProgram
import unittest
import mock
import numpy
import u3


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


class TestGenSize(unittest.TestCase):

    def test_is_image(self):
        stim = StimProgram.StaticStim(fill_mode='image',
                                      image_size=[100,100])
        self.assertTupleEqual(stim.gen_size(), (100, 100))

    def test_is_rectangle(self):
        stim = StimProgram.StaticStim(shape='rectangle',
                                      size=[100, 200])
        self.assertTupleEqual(stim.gen_size(), (100, 200))

    def test_is_annulus(self):
        stim = StimProgram.StaticStim(shape='annulus',
                                      outer_diameter=40,
                                      inner_diameter=10)
        self.assertTupleEqual(stim.gen_size(), (40, 40))


class TestGenMask(unittest.TestCase):

    def test_is_annulus(self):
        stim = StimProgram.StaticStim(shape='annulus')
        self.assertEqual(stim.gen_mask(), 'circle')

    def test_is_circle(self):
        stim = StimProgram.StaticStim(shape='circle')
        self.assertEqual(stim.gen_mask(), 'circle')

    def test_is_rectangle(self):
        stim = StimProgram.StaticStim(shape='rectangle')
        self.assertIsNone(stim.gen_mask())


class TestGenRGB(unittest.TestCase):

    def test_bg0_mode_rgb(self):
        stim = StimProgram.StaticStim(contrast_channel='green',
                                      color_mode='rgb',
                                      color=[1, 1, 1],
                                      alpha=1)

        self.assertTupleEqual(stim.gen_rgb()[2:], (0.5, 0.5))
        numpy.allclose(stim.gen_rgb()[0], numpy.array([1, 1, 1, 1]))
        numpy.allclose(stim.gen_rgb()[1], numpy.array([0, 0.5, 0, 1]))

    def test_bg0_mode_intensity_both(self):
        stim = StimProgram.StaticStim(contrast_channel='green',
                                      color_mode='intensity',
                                      intensity_dir='both',
                                      intensity=1,
                                      color=[1, 1, 1],
                                      alpha=1)

        self.assertTupleEqual(stim.gen_rgb()[2:], (0.5, 0.5))
        numpy.allclose(stim.gen_rgb()[0], numpy.array([1]))
        numpy.allclose(stim.gen_rgb()[1], numpy.array([-1]))

    def test_bg0_mode_negintensity_both(self):
        stim = StimProgram.StaticStim(contrast_channel='green',
                                      color_mode='intensity',
                                      intensity_dir='both',
                                      intensity=-1,
                                      color=[1, 1, 1],
                                      alpha=1)

        self.assertTupleEqual(stim.gen_rgb()[2:], (-0.5, 0.5))
        numpy.allclose(stim.gen_rgb()[0], numpy.array([-1]))
        numpy.allclose(stim.gen_rgb()[1], numpy.array([1]))

    def test_bg0_mode_intensity_single(self):
        stim = StimProgram.StaticStim(contrast_channel='green',
                                      color_mode='intensity',
                                      intensity_dir='single',
                                      intensity=1,
                                      color=[1, 1, 1],
                                      alpha=1)

        self.assertTupleEqual(stim.gen_rgb()[2:], (0.25, 0.75))
        numpy.allclose(stim.gen_rgb()[0], numpy.array([1]))
        numpy.allclose(stim.gen_rgb()[1], numpy.array([0]))

    def test_bg0_mode_negintensity_single(self):
        stim = StimProgram.StaticStim(contrast_channel='green',
                                      color_mode='intensity',
                                      intensity_dir='single',
                                      intensity=-1,
                                      color=[1, 1, 1],
                                      alpha=1)

        self.assertTupleEqual(stim.gen_rgb()[2:], (-0.25, 0.25))
        numpy.allclose(stim.gen_rgb()[0], numpy.array([-1]))
        numpy.allclose(stim.gen_rgb()[1], numpy.array([0]))


if __name__ == '__main__':
    unittest.main()