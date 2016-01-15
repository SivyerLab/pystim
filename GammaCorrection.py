#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Script for setting the gamma correction table for psychopy. Steps through
luminosity intervals while user records values, then prompts for table. Table is
text file, with newline seperated values, and each color (in RGB order),
seperated by 2 new lines.

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

Currently, in OSX, the calibrate button in the GUI is unable to invoke the
script, but instead brings up a terminal window in the correct location,
and the script can be started by entering (note .pyc, not .py)::

    python GammaCorrection.pyc
"""

from psychopy import visual, core, event, logging
from psychopy.monitors import Monitor
from scipy import stats, interpolate, array, ndarray
import matplotlib.pyplot as plt
import cPickle
import os.path
import sys

# suppress extra warnings
logging.console.setLevel(logging.CRITICAL)

def gammaCorrect():
    """
    Main function.

    :return: Nothing.
    """
    prompt = True

    while prompt:
        num_steps = '30'# num_steps = raw_input('\nNumber of steps per gun?').rstrip()

        if num_steps.isdigit():
            num_steps = int(num_steps)
            should_step = 'N' #should_step = raw_input('Run through RGB steps
            #  for each gun? Y, N: ').rstrip()

            if should_step == 'Y':
                should_step = True
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

    colors = [i * 1.0 / num_steps * 2 - 1 for i in range(num_steps+1)]
    # print len(colors)
    # print colors

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

    inputs = [(i+1)/2 for i in colors]

    # print '\nEnter lums into a text file. Each entry separated by new line, ' \
    #       'colors seperated by 2 new lines, in RGB order.'
    # lums = raw_input('Enter file location: ').rstrip()
    lums = 'C:\\Users\\Alex\\PycharmProjects\\StimProgram\\psychopy' \
           '\\gammaTable.txt'
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
    plt.legend(loc=0)
    # plt.show()

    gamma_correction = GammaValues(r_tuple, g_tuple, b_tuple)

    ## GRAPHING STUFF TO TEST ##
    vals = [i * 1.0 / (51 - 1) * 2 - 1 for i in range(51)]
    corrected = [[], [], []]
    for i in range(len(vals)):
        rgb = [vals[i]] * 3
        rgb = gamma_correction(rgb)
        corrected[0].append(rgb[0])
        corrected[1].append(rgb[1])
        corrected[2].append(rgb[2])

    plt.plot(vals, vals, 'k--', label='linear')
    plt.plot(vals, corrected[0], 'r', label='red')
    plt.plot(vals, corrected[1], 'g', label='green')
    plt.plot(vals, corrected[2], 'b', label='blue')
    plt.legend(loc=0)
    # plt.show()

    should_save = raw_input('\nSave? Y, N: ')

    gamma_file = './psychopy/gammaTables.txt'

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
    Calculates a conversion of RGB values to appropriate values to linearize
    screen luminosity.

    :param list measured: Recorded values of screen luminosity. Passed by \
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
    to_plot.append(plt.plot(measured_at, measured, 'ro', label='measured'))
    # fit
    to_plot.append(plt.plot(measured_at, spline_values, label='interpolated'))
    # corrected
    to_plot.append(plt.plot(measured_at, graph_corrected, label='corrected'))
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

    def __call__(self, rgb):
        """
        Calculates adjusted RGB value.

        :param list rgb: List of RGB values, scaled from -1 to 1.
        :return: Adjusted list of RGB values
        """
        r = rgb[0]
        g = rgb[1]
        b = rgb[2]

        r_adj = float(self.r_spline(r * self.r_slope + self.r_int))
        g_adj = float(self.g_spline(g * self.g_slope + self.g_int))
        b_adj = float(self.b_spline(b * self.b_slope + self.b_int))

        adj_rgb = [r_adj, g_adj, b_adj]

        for i in range(3):
            if adj_rgb[i] >= 1:
                adj_rgb[i] = 1
            elif adj_rgb[i] <= -1:
                adj_rgb[i] = -1

        return adj_rgb

if __name__ == "__main__":
    gammaCorrect()