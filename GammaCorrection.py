#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Script for setting the gamma correction table for psychopy. Steps through
luminosity intervals while user records values, then prompts for table.
Can skip the luminosity stepping and go straight to table. Table is
text file, with newline separated values, and each color (in RGB order)
separated by 2 new lines.

Example::

    0.22
    0.23
    0.23
    0.25
    0.26

    0.22
    0.23
    0.24
    0.26
    0.27

    0.22
    0.23
    0.23
    0.24
    0.25

The script can be invoked from the command line/terminal::

    python GammaCorrection.py

Psychopy has built in gamma correction. This script provides an alternative
to that due to difficulties using it with a second monitor on some platforms.
See the psychopy documentation for information on using the built in gamma
correction.
"""

from psychopy import visual, core, logging
from psychopy.monitors import Monitor
from scipy import stats, interpolate, array, ndarray
import cPickle
import os.path
import numpy
import sys
import copy_reg, types
# import matplotlib.pyplot as plt

# suppress extra warnings
logging.console.setLevel(logging.CRITICAL)


# def reduce_method(m):
#     """
#     Method to allow pickling
#     """
#     return (getattr, (m.__self__, m.__func__.__name__))
#
# copy_reg.pickle(types.MethodType, reduce_method)


def gammaCorrect():
    """
    Prompts user for inputs. Generates evenly spaced RGB values in each gun
    if user desires. Gets splines and prompts for saving.
    """
    prompt = True

    while prompt:
        should_step = raw_input('Run through RGB steps for each gun? Y, '
                                'N: ').rstrip()

        if should_step == 'Y':
            should_step = True
            mon_name = raw_input('Gamma profile to use? None or name: ')

            num_steps = raw_input('\nNumber of steps per gun? ').rstrip()

            if num_steps.isdigit():
                num_steps = int(num_steps)
                colors = [i * 1.0 / num_steps * 2 - 1 for i in range(num_steps+1)]
                inputs = [(i+1)/2 for i in colors]

                step_time = raw_input('Time between steps (ms)? ').rstrip()

                if step_time.isdigit():
                    step_time = int(step_time)

                    screen_num = raw_input('Screen number? ').rstrip()

                    if screen_num.isdigit():
                        screen_num = int(screen_num)

                        should_flash = raw_input('Flash black? Y, N: ')

                        if should_flash == 'Y':
                            should_flash = True
                            prompt = False

                        elif should_flash == 'N':
                            should_flash = False
                            prompt = False

        elif should_step == 'N':
            should_step = False
            prompt = False
        else:
            print '\nAnswer correctly.'

    if should_step:
        win = visual.Window(monitor='testMonitor', fullscr=False,
                            screen=screen_num, winType='pyglet',
                            units='norm')
        rect = visual.Rect(win, width=2.1, height=2.1, fillColorSpace='rgb',
                           fillColor=(-1, -1, -1))

        rgb = ['RED', 'GREEN', 'BLUE']

        for i in range(3):
            raw_input("\n{}\npress enter to proceed when ready...".format(rgb[i])).rstrip()

            for color in colors:
                fill = [-1, -1, -1]
                if should_flash:
                    for x in range(5):
                        rect.setFillColor(fill)
                        rect.draw()
                        win.flip()
                fill[i] = color
                rect.setFillColor(fill)
                rect.draw()
                win.flip()
                core.wait(step_time * 1.0 /1000)

        win.close()

    print '\nEnter lums into a text file. Each entry separated by new line, ' \
          'colors seperated by 2 new lines, in RGB order.'
    lums = raw_input('Enter file location: ').rstrip()
    try:
        with open(lums, 'r') as f:
            rgbs = f.read()
            rgbs = rgbs.replace('\r', '')
    except IOError:
        print '\n File not found. Restarting. \n'
        gammaCorrect()

    rgbs = rgbs.split('\n\n')
    r = rgbs[0].split('\n')
    g = rgbs[1].split('\n')
    b = rgbs[2].split('\n')

    r = map(float, r)
    g = map(float, g)
    b = map(float, b)

    mon = raw_input('\nMonitor to edit: ')

    r_tuple = make_correction(r)
    g_tuple = make_correction(g)
    b_tuple = make_correction(b)

    # show_plot = raw_input('\nShow plots? Y, N: ')
    # if show_plot == 'Y':
    #     plt.legend(loc=0)
    #     plt.show()

    gamma_correction = GammaValues(r_tuple, g_tuple, b_tuple)

    ## GRAPHING STUFF TO TEST ##
    # vals = [i * 1.0 / (51 - 1) * 2 - 1 for i in range(51)]
    # corrected = [[], [], []]
    # for i in range(len(vals)):
    #     rgb = [vals[i]] * 3
    #     rgb = gamma_correction(rgb)
    #     corrected[0].append(rgb[0])
    #     corrected[1].append(rgb[1])
    #     corrected[2].append(rgb[2])
    #
    # if show_plot == 'Y':
    #     plt.plot(vals, vals, 'k--', label='linear')
    #     plt.plot(vals, corrected[0], 'r', label='red')
    #     plt.plot(vals, corrected[1], 'g', label='green')
    #     plt.plot(vals, corrected[2], 'b', label='blue')
    #     plt.legend(loc=0)
    #     plt.show()

    should_save = raw_input('\nSave? Y, N: ')

    gamma_file = './psychopy/data/gammaTables.txt'

    if should_save == 'Y':
        if os.path.exists(gamma_file):
            with open(gamma_file, 'rb') as f:
                gamma_dict = cPickle.load(f)
            print 'existing:',
            for k, v in gamma_dict.iteritems():
                print k + ',',
            gamma_dict[mon] = gamma_correction

        else:
            gamma_dict = {mon: gamma_correction}

        with open(gamma_file, 'wb') as f:
            cPickle.dump(gamma_dict, f)

        print '\n Gamma correction saved. Done.'

    else:
        print 'Done.\n'


def make_correction(measured):
    """
    Calculates a conversion spline of RGB values to corrected values to
    linearize screen luminosity.

    :param list measured: Recorded values of screen luminosity. Passed by
     gammaCorrect, pulled out of text file.
    :return: Tuple of spline, slope, and intercept
    """
    # values where lum was measured, assuming even spacing and starting at
    # min and max
    measured_at = [i * 1.0 / (len(measured) - 1) * 2 - 1
                   for i in range(len(measured))]

    # for spline, x must be increasing, so do check on values
    is_increasing = [x<y for x, y in zip(measured, measured[1:])]

    # remove non increasing values, going backwards to not change indices
    for i in range(len(is_increasing) - 1, -1, -1):
        if not is_increasing[i]:
            del measured[i+1]
            del measured_at[i+1]

    min = measured[0]
    max = measured[-1]

    # line to linearize to
    slope, intercept, _, _, _ = stats.linregress([-1.0, 1.0], [min, max])

    # splines to fit to data
    spline = interpolate.InterpolatedUnivariateSpline(measured_at, measured)
    inverse_spline = interpolate.InterpolatedUnivariateSpline(measured,
                                                              measured_at)

    # ##GRAPHING STUFF TO TEST##
    linear = [i * slope + intercept for i in measured_at]
    spline_values = spline([i for i in measured_at])
    corrected_values = inverse_spline([i * slope + intercept for i in measured_at])
    graph_corrected = spline([i for i in corrected_values])

    # for i in range(len(corrected_values)):
    #     print "%.3f" % measured_at[i], "%.3f" % corrected_values[i]

    to_plot = []
    # points
    # to_plot.append(plt.plot(measured_at, measured, 'ro', label='measured'))
    # fit
    # to_plot.append(plt.plot(measured_at, spline_values, label='interpolated'))
    # corrected
    # to_plot.append(plt.plot(measured_at, graph_corrected, label='corrected'))
    # check against linear
    # to_plot.append(plt.plot(measured_at, linear, label='linear'))
    # plt.legend(loc=0)
    # plt.show()

    return inverse_spline, slope, intercept, to_plot

class GammaValues(object):
    """
    Class to hold values for gamma correcting and returning calculations.

    :param tuple r: Tuple of spline, slope, intercept for red gun
    :param tuple g: Tuple of spline, slope, intercept for green gun
    :param tuple b: Tuple of spline, slope, intercept for blue gun
    """
    def __init__(self, r, g, b):
        """
        Instantiates class, pulls values out of tuples.
        """
        self.r_spline = r[0]
        self.r_slope = r[1]
        self.r_int = r[2]

        self.g_spline = g[0]
        self.g_slope = g[1]
        self.g_int = g[2]

        self.b_spline = b[0]
        self.b_slope = b[1]
        self.b_int = b[2]

    def r_correct(self, r):
        """
        Method to gamma correct red channel.

        :return: corrected red color
        """
        r_adj = self.r_spline(r * self.r_slope + self.r_int)
        return r_adj

    def g_correct(self, g):
        """
        Method to gamma correct green channel.

        :return: corrected green color
        """
        # print g
        # print type(g)
        g_adj = self.g_spline(g * self.g_slope + self.g_int)
        return g_adj

    def b_correct(self, b):
        """
        Method to gamma correct blue channel.

        :return: corrected blue color
        """
        b_adj = self.b_spline(b * self.b_slope + self.b_int)
        return b_adj

    def __call__(self, color, channel=None):
        """
        Calculates adjusted color value. Allows getting corrected values by
        making calls to instance.

        :param list color: List of RGB values, scaled from -1 to 1, or color
         from a single channel.
        :param int channel: If color is passed as a single number, channel is
         the color channel.
        :return: Adjusted list of RGB values, or single adjusted color.
        """
        if channel is None:
            # if entire texture
            if len(numpy.shape(color)) == 3:
                has_alpha = bool(numpy.shape(color)[2] == 4)

                adj_color = numpy.copy(color)

                size = adj_color.shape[0]

                if has_alpha:
                    r, g, b, a = numpy.split(adj_color, 4, axis=2)
                else:
                    r, g, b = numpy.split(adj_color, 3, axis=2)

                r = r.flatten()
                g = g.flatten()
                b = b.flatten()
                if has_alpha:
                    a = a.flatten()

                print 'red correcting.....',
                r = self.r_correct(r)
                print 'done'
                print 'green correcting...',
                g = self.g_correct(g)
                print 'done'
                print 'blue correcting....',
                b = self.b_correct(b)
                print 'done\n'

                if has_alpha:
                    adj_color = numpy.dstack([numpy.split(r, size),
                                              numpy.split(g, size),
                                              numpy.split(b, size),
                                              numpy.split(a, size)])
                else:
                    adj_color = numpy.dstack([numpy.split(r, size),
                                              numpy.split(g, size),
                                              numpy.split(b, size)])

            # if single color
            elif len(numpy.shape(color)) == 1:
                # ignore alpha
                r = color[0]
                g = color[1]
                b = color[2]

                print 'red correcting.....',
                r_adj = self.r_correct(r)
                print 'done'
                print 'green correcting...',
                g_adj = self.g_correct(g)
                print 'done'
                print 'blue correcting....',
                b_adj = self.b_correct(b)
                print 'done\n'

                adj_color = color[:]

                adj_color[0] = r_adj
                adj_color[1] = g_adj
                adj_color[2] = b_adj

                # add ceiling/floor
                for i in range(len(color)):
                    if adj_color[i] >= 1:
                         adj_color[i] = 1.0
                    elif adj_color[i] <= -1:
                         adj_color[i] = -1.0

            # if grayscale image
            elif len(numpy.shape(color)) == 2:
                print '\nWARNING: Cannot gamma correct grayscale .iml images.'
                adj_color = color

        # if single channel
        elif channel is not None:
            if channel == 0:
                # print 'red correcting.....',
                adj = self.r_correct(color)
                # print 'done'
            if channel == 1:
                # print 'green correcting...',
                adj = self.g_correct(color)
                # print 'done'
            if channel == 2:
                # print 'blue correcting....',
                adj = self.b_correct(color)
                # print 'done'

            adj_color = adj

            # add ceiling/floor
            if adj_color >= 1:
                adj_color = 1.0
            elif adj_color <= -1:
                adj_color = -1.0

        return adj_color

if __name__ == "__main__":
    gammaCorrect()