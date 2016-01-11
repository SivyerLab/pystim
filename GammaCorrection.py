from psychopy import visual, core, event, logging
from psychopy.monitors import Monitor
from psychopy.monitors.calibTools import GammaCalculator
import numpy as np

# suppress extra warnings
logging.console.setLevel(logging.CRITICAL)

def gammaCorrect():
    prompt = True

    while prompt:
        should_step = raw_input('Run through RGB steps for each gun? Y, '
                                'N: ').rstrip()
        if should_step == 'Y':
            should_step = True
            num_steps = raw_input('Number of steps per gun? ').rstrip()
            if num_steps.isdigit():
                num_steps = int(num_steps)
                step_time = raw_input('Time between steps (ms)? ').rstrip()
                if step_time.isdigit():
                    step_time = int(step_time)
                    screen_num = raw_input('Screen number? ').rstrip()
                    if screen_num.isdigit():
                        screen_num = int(screen_num)
                        prompt = False
        elif should_step == 'N':
            should_step = False
            prompt = False
        else:
            print 'Enter Y or N.'

    if should_step:
        win = visual.Window(monitor='testMonitor', fullscr=False,
                            screen=screen_num, winType='pyglet',
                            units='norm')
        rect = visual.Rect(win, width=2.1, height=2.1, fillColorSpace='rgb',
                           fillColor=(-1, -1, -1))

        colors = [i * 1.0 / num_steps * 2 - 1 for i in range(num_steps+1)]
        print len(colors)
        # print colors

        rgb = ['RED', 'GREEN', 'BLUE']

        for i in range(3):
            raw_input("\n{}\npress enter to proceed when ready...".format(rgb[
                                                                             i])).rstrip()
            for color in colors:
                fill = [-1, -1, -1]
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

        with open(lums, 'r') as f:
            rgbs = f.read()

        rgbs = rgbs.split('\n\n')
        r = rgbs[0].split('\n')
        g = rgbs[1].split('\n')
        b = rgbs[2].split('\n')

        mon_name = raw_input('\nMonitor to edit: ')
        mon = Monitor(mon_name)

        r = [float(i) * 10 for i in r]
        g = [float(i) * 10 for i in g]
        b = [float(i) * 10 for i in b]

        r = GammaCalculator(inputs, r, eq=4).gammaModel
        g = GammaCalculator(inputs, g, eq=4).gammaModel
        b = GammaCalculator(inputs, b, eq=4).gammaModel

        grid = np.empty((4,6))

        for x in np.nditer(grid, op_flags=['readwrite']):
            x[...] = np.nan

        grid[0][0] = 0; grid[1][0] = 0; grid[2][0] = 0; grid[3][0] = 0
        grid[0][1] = 1; grid[1][1] = 1; grid[2][1] = 1; grid[3][1] = 1
        grid[0][2]=1

        grid[1][2] = r[0]
        grid[1][3] = r[1]
        grid[1][5] = r[2]

        grid[2][2] = g[0]
        grid[2][3] = g[1]
        grid[2][5] = g[2]

        grid[3][2] = b[0]
        grid[3][3] = b[1]
        grid[3][5] = b[2]

        print '\nGamma correction model: a+kx^g'
        print 'Red:   g = {}'.format(r[0])
        print '       a = {}'.format(r[1])
        print '       k = {}'.format(r[2])
        print 'Green: g = {}'.format(g[0])
        print '       a = {}'.format(g[1])
        print '       k = {}'.format(g[2])
        print 'Blue : g = {}'.format(b[0])
        print '       a = {}'.format(b[1])
        print '       k = {}'.format(b[2])

        should_save = raw_input('\nSave? Y or N: ').rstrip()

        if should_save == 'Y':
            mon.setGammaGrid(grid)
            mon.saveMon()
            print '\ngamma grid set'
        #
        # print mon.getGammaGrid()

if __name__ == "__main__":
    gammaCorrect()