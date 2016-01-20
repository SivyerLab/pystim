from PIL import Image
from psychopy import visual, core
from random import Random
import numpy as np

def transition():
    my_win = visual.Window()
    buffering = visual.TextStim(my_win, text='buffering...')
    buffering.draw()
    my_win.flip()

    image1 = Image.open(r"C:\Users\Alex\PycharmProjects\StimProgram\psychopy"
                        r"\forest1.jpg")
    image2 = Image.open(r"C:\Users\Alex\PycharmProjects\StimProgram\psychopy"
                        r"\forest2.jpg")


    image1 = image1.crop((0, 0, image1.size[0], image2.size[1]))
    image2 = image2.crop((0, 0, image1.size[0], image1.size[1]))

    img_list = []
    alpha = 0

    while alpha < 1.0:
        trans_img = Image.blend(image1, image2, alpha)
        trans_img.thumbnail((800, 600), Image.ANTIALIAS)
        alpha += 0.05
        pic = visual.SimpleImageStim(win=my_win, image=trans_img)
        pic.draw()
        img_list.append(visual.BufferImageStim(my_win))

    for i in img_list:
        i.draw()
        my_win.flip()
        core.wait(0.1)

    core.wait(1)

    my_win.close()

def jump():
    my_win = visual.Window()
    buffering = visual.TextStim(my_win, text='buffering...')
    buffering.draw()
    my_win.flip()

    image1 = Image.open(r"C:\Users\Alex\PycharmProjects\StimProgram\psychopy"
                        r"\forest1.jpg")
    cropped_list = []
    img_list = []

    rand = Random()
    rand.seed(2)

    num_jumps = 10

    for i in range(num_jumps):
        x = rand.randint(0, image1.size[0]-800)
        y = rand.randint(0, image1.size[1]-600)
        cropped = image1.crop((x, y, x+800, y+600))
        cropped_list.append(cropped)
        pic = visual.SimpleImageStim(win=my_win, image=cropped)
        pic.draw()
        img_list.append(visual.BufferImageStim(my_win))


    pic = visual.SimpleImageStim(win=my_win, image=merge(cropped_list))
    img_list.append(pic)

    for i in img_list:
        i.draw()
        my_win.flip()
        core.wait(0.5)

    core.wait(3)

    my_win.close()

def merge(img_list):
    w, h = img_list[0].size
    N = len(img_list)

    average = np.zeros((h, w, 3), np.float)

    for img in img_list:
        img_array = np.array(img, dtype=np.float)
        average += img_array / N

    average = np.array(np.round(average), dtype=np.uint8)

    return Image.fromarray(average, mode='RGB')


if __name__ == '__main__':
    jump()