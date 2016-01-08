from psychopy.monitors import Monitor
from psychopy.monitors.calibTools import GammaCalculator
from psychopy import visual, core


prompt = True

while prompt:
    should_step = raw_input('Run through RGB steps for each gun? Y, N: ')

    if should_step == 'Y':
        should_step = True
        num_steps = raw_input('Number of steps per gun? ')
        if num_steps.isdigit():
            num_steps = int(num_steps) + 1
            step_time = raw_input('Time between steps (ms)? ')
            if step_time.isdigit():
                step_time = int(step_time)
                screen_num = raw_input('Screen number? ')
                if screen_num.isdigit():
                    screen_num = int(screen_num)
                    prompt = False
    elif should_step == 'N':
        should_step = False
        prompt = False
    else:
        print 'Enter Y or N.'

if should_step:
    win = visual.Window(monitor='testMonitor', fullscr=True,
                        screen=screen_num, winType='pyglet',
                        units='norm')
    rect = visual.Rect(win, width=2.1, height=2.1, fillColorSpace='rgb',
                       fillColor=(-1, -1, -1))

    colors = [i * 1.0 / num_steps * 2 - 1 for i in range(num_steps)]
    # print colors

    print '\nRED'
    raw_input("press enter to when ready...")

    for color in colors:
        rect.setFillColor((color, -1, -1))
        rect.draw()
        win.flip()
        core.wait(step_time * 1.0 /1000)

    print '\nGREEN'
    raw_input("press enter to when ready...")

    for color in colors:
        rect.setFillColor((-1, color, -1))
        rect.draw()
        win.flip()
        core.wait(step_time * 1.0 /1000)

    print '\nBLUE'
    raw_input("press enter to when ready...")

    for color in colors:
        rect.setFillColor((-1, -1, color))
        rect.draw()
        win.flip()
        core.wait(step_time * 1.0 /1000)

    inputs = [(i+1)/2 for i in colors]

