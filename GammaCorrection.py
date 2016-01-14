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
and the script can be started by entering (note .pyc, not .py):
::
    python GammaCorrection.pyc
"""

from psychopy import visual, core, event, logging
from psychopy.monitors import Monitor
from scipy import stats, interpolate
import matplotlib.pyplot as plt

# suppress extra warnings
logging.console.setLevel(logging.CRITICAL)

def gammaCorrect():
    """
    Main function.

    :return: Nothing.
    """
    prompt = True

    while prompt:
        num_steps = raw_input('\nNumber of steps per gun? ').rstrip()

        if num_steps.isdigit():
            num_steps = int(num_steps)
            should_step = raw_input('Run through RGB steps for each gun? Y, '
                                    'N: ').rstrip()

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

    mon_name = raw_input('\nMonitor to edit: ')
    mon = Monitor(mon_name)

    make_correction(r)
    make_correction(g)
    make_correction(b)

def make_correction(measured):
    min = measured[0]
    max = measured[-1]

    measured_at = [i * 1.0 / (len(measured) - 1) * 2 - 1 for i in range(len(measured))]

    slope, intercept, _, _, _ = stats.linregress([-1.0, 1.0], [min, max])

    spline = interpolate.InterpolatedUnivariateSpline(measured_at, measured)
    inverse_spline = interpolate.InterpolatedUnivariateSpline(measured,
                                                              measured_at)

    # GRAPHING STUFF TO TEST
    spline_values = [spline(i) for i in measured_at]
    corrected_values = [inverse_spline(i * slope + intercept) for i in measured_at]
    graph_corrected = [spline(i) for i in corrected_values]

    # points
    plt.plot(measured_at, measured, 'ro', label='measured')
    # fit
    plt.plot(measured_at, spline_values, label='interpolated')
    # corrected
    plt.plot(measured_at, graph_corrected, label='corrected')

    plt.legend(loc=0)
    plt.show()

    return (inverse_spline, slope, intercept)


if __name__ == "__main__":
    gammaCorrect()