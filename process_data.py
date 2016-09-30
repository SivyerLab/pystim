"""Processes spike data and frames to generate receptive field map"""

from __future__ import division

print 'Importing...'

from heka_reader import Bundle
from tqdm import tqdm
from pandas import cut
import numpy as np
from PIL import Image

from spike_sort.core.extract import detect_spikes
import ast
import cv2
import os
import re

from collections import deque


def get_weights(dat_file,
                group,
                series,
                sweep,
                data_trace,
                trigger_trace,
                thresh,
                center_on,
                window,
                latency=None):
    """
    Calculates spikes per image interval

    :param dat_file: data
    :param int group:
    :param int series:
    :param sweep: int or iterable
    :param int data_trace:
    :param int trigger_trace:
    :param thresh: str(int)
    :param string center_on: 'max' or 'min'
    :param float window:
    :param float latency: in ms
    :return: ndarray of weights
    """
    print '\nProcessing wave data...'
    group -= 1
    series -= 1

    try:
        sweeps = map(lambda x: x - 1, sweep)
    except TypeError:
        sweeps = [sweep - 1]

    data_trace -= 1
    trigger_trace -= 1

    # get bundle
    bundle = Bundle(dat_file)

    # get data from bundle
    trace_data = [bundle.data[group, series, i, data_trace] for i in sweeps]
    trigger_data = [bundle.data[group, series, i, trigger_trace] for i in
                    sweeps]
    x_int = bundle.pul[group][series][sweeps[0]][data_trace].XInterval

    # prep for spike sort
    trace_raw = {
        'data': np.array(trace_data),
        'FS': int(round(1 / x_int)),
        'n_contacts': len(trace_data)
        }

    trigger_raw = {
        'data': np.array(trigger_data),
        'FS': int(round(1 / x_int)),
        'n_contacts': len(trigger_data)
        }

    print '\nDetecting spikes...'
    if center_on == 'max':
        trace_spts = [detect_spikes(trace_raw,
                                    thresh=thresh,
                                    edge='rising',
                                    contact=i)['data'] for i in range(len(sweeps))]
    if center_on == 'min':
        trace_spts = [detect_spikes(trace_raw,
                                    thresh=thresh,
                                    edge='falling',
                                    contact=i)['data'] for i in range(len(sweeps))]

    print 'Detecting triggers...'
    trigger_spts = [detect_spikes(trigger_raw,
                                  thresh='4',
                                  edge='rising',
                                  contact=i)['data'] for i in range(len(sweeps))]

    # data window
    half_window = int(window / 1000 / x_int)
    trace_spike_indices = []

    # adjust spike times
    print '\nAdjusting spike times...'
    for index, trace_spt in enumerate(trace_spts):
        indices = []
        for time in trace_spt:
            # turn ms time into index
            ar_index = int(round(time / 1000 / x_int))
            # make window around guess at peak
            window = trace_data[index][ar_index - half_window:
                                       ar_index + half_window]
            # get index of local min/max
            # try in case peak is at bounds of data
            try:
                if center_on == 'max':
                    peak_index = np.argmax(window) + ar_index - half_window
                elif center_on == 'min':
                    peak_index = np.argmin(window) + ar_index - half_window
            except ValueError:
                continue

            indices.append(peak_index)

        print '    num spikes:', len(indices)
        trace_spike_indices.append(np.array(indices))

    trace_spike_indices = np.array(trace_spike_indices)

    # trigger 1 ms window
    half_window = int(1 / 1000 / x_int)
    trigger_spike_indices = []

    # adjust tirgger times
    print 'Adjusting trigger times...'
    for index, trace_spt in enumerate(trigger_spts):
        indices = []
        for time in trace_spt:
            # turn ms time into index
            ar_index = int(time / 1000 * round(1 / x_int))
            # make window around guess at peak
            window = trigger_data[index][ar_index - half_window:
                                         ar_index + half_window]
            # get index of local max
            # try in case peak is at bounds of data
            try:
                peak_index = np.argmax(window) + ar_index - half_window
            except ValueError:
                continue

            indices.append(peak_index)

        print '   num triggers:', len(indices)
        trigger_spike_indices.append(np.array(indices))

    trigger_spike_indices = np.array(trigger_spike_indices)

    # get mode of length of trigger indices (in case of extra triggers at end)
    lengths = [i.shape[0] for i in trigger_spike_indices]
    mode = max(set(lengths), key=lengths.count) - 1

    weights = np.zeros((len(trigger_spike_indices), mode), dtype=np.int32)

    # bin spikes
    print '\nBinning spikes...'
    for i, trigger_indices in enumerate(trigger_spike_indices):

        if latency is not None:
            trace_spike_indices[i] -= int(round(latency / 1000 / x_int))

        # cut makes bins out of trigger indices and bins spike indices
        ret = cut(trace_spike_indices[i], trigger_indices, labels=False,
                  right=False)
        ret = ret[~np.isnan(ret)].astype(np.int32)
        # count incidents of bins
        bincount = np.bincount(ret)[:mode]

        dif = weights[i].shape[0] - bincount.shape[0]

        if dif != 0:
            bincount = np.append(bincount, [0] * dif)

        weights[i] = bincount

        # print 'triggers:', trigger_indices[:5]*x_int
        # print weights[i][:10]
        # print np.sum(weights[i])

    print 'Done'
    return weights


class Slicer(object):
    def __init__(self, file):

        self.slice_locs = []

        with open(file, 'rb') as f:
            self.image_filename = f.readline().lstrip('image: ').rstrip()
            self.shuffle = f.readline().lstrip('shuffle: ').rstrip() == 'True'
            self.image_channel = ['red', 'green', 'blue', 'all'][int(
                f.readline().lstrip('image_channel: ').rstrip())]

            self.image_size = ast.literal_eval(
                f.readline().lstrip('image_size: ').rstrip())
            self.num_jumps = ast.literal_eval(
                f.readline().lstrip('num_jumps: ').rstrip())
            self.move_seed = ast.literal_eval(
                f.readline().lstrip('move_seed: ').rstrip())

            self.display_size = ast.literal_eval(
                f.readline().lstrip('window_size: ').rstrip())
            self.offset = ast.literal_eval(
                f.readline().lstrip('offset: ').rstrip())
            self.trigger_wait = ast.literal_eval(
                f.readline().lstrip('trigger_wait: ').rstrip())
            self.gamma_correction = re.sub('^gamma_correction: ',
                                           '', f.readline().rstrip())

            f.readline()
            f.readline()
            f.readline()
            for line in f:
                line = line.rstrip().rstrip('|').lstrip('|')
                line = map(int, line.split('|'))
                self.slice_locs.append(line)

        del self.slice_locs[-1]
        self.slice_locs = np.array(self.slice_locs)

    def __str__(self):
        to_print = ''

        to_print += '\nSlice list:'
        to_print += '\n    image_file: {}'.format(self.image_filename)
        to_print += '\n    shuffle: {}'.format(self.shuffle)
        to_print += '\n    image_channel: {}'.format(self.image_channel)
        to_print += '\n    image_size: {}'.format(self.image_size)
        to_print += '\n    num_jumps: {}'.format(self.num_jumps)
        to_print += '\n    move_seed: {}'.format(self.move_seed)
        to_print += '\n'
        to_print += '\n    display_size: {}'.format(self.display_size)
        to_print += '\n    offset: {}'.format(self.offset)
        to_print += '\n    trigger_wait: {}'.format(self.trigger_wait)
        to_print += '\n    gamma_correction: {}'.format(self.gamma_correction)

        return to_print


def get_slices_texs(folder, which='all'):
    """
    Gets slices from file

    :param folder: folder with slices and numpy arrays
    :param which: which sweeps to include
    :return:
    """
    # print folder
    try:
        folder = os.path.abspath(folder)
        files = os.listdir(folder)
        files = map(lambda x: os.path.join(folder, x), files)

    except (TypeError, AttributeError):  # win: TypeError, darwin: AttrError
        files = []
        for fold in folder:
            fold = os.path.abspath(fold)
            paths = os.listdir(fold)
            paths = map(lambda x: os.path.join(fold, x), paths)
            files += paths

    log_files = [i for i in files if os.path.splitext(i)[1] == '.txt' and
                 os.path.basename(i).startswith('Jumpinglog')]

    tex_files = [i for i in files if os.path.splitext(i)[1] == '.npy']

    if which != 'all':
        # which is not zero indexed; adjust
        try:
            log_files = [log_files[i - 1] for i in range(len(which))]
            tex_files = [tex_files[i - 1] for i in range(len(which))]
        except TypeError:
            log_files = [log_files[which - 1]]
            tex_files = [tex_files[which - 1]]

    slices = [Slicer(log) for log in log_files]

    return slices, tex_files


def get_rec_field(slices, texs, weights, num_frames=3):
    """

    :param slices:
    :param weights:
    :return:
    """
    sum_weights = 0
    for j in weights:
        sum_weights += np.sum(j)

    cap_sum = np.zeros((slices[0].display_size[1],
                        slices[0].display_size[0],
                        4), dtype=np.float64)

    counter = 0

    print '\nBuilding receptive field...'
    for i, slice in enumerate(slices):
        tex = np.load(texs[i]).astype(np.float64)

        slice_deque = deque([], maxlen=num_frames)

        for j, slice_ind in enumerate(tqdm(slice.slice_locs)):
            tex_slice = tex[slice_ind[0]:slice_ind[1],
                            slice_ind[2]:slice_ind[3]]

            slice_deque.append(tex_slice)

            for deq_slice in slice_deque:
                cap_sum += (deq_slice * weights[i][j])
                counter += weights[i][j]

    # cap_sum /= sum_weights
    cap_sum /= counter
    print counter, sum_weights
    cap_sum = cap_sum.astype(np.uint8)

    print 'Done'
    return cap_sum


def main(**kwargs):

    slices, texs = get_slices_texs(folder=kwargs['jump_logs'],
                                   # which=[1, 3, 5]
                                   # which='all'
                                   which=kwargs['sweep']
                                   )

    kwargs.pop('jump_logs')
    num_frames = kwargs.pop('num_frames')

    weights = get_weights(**kwargs)

    rec_field = get_rec_field(slices, texs, weights, num_frames)
    return rec_field
    # cv2.imwrite('rec_field.png', rec_field.copy())

    # scale = 1
    # disp = cv2.resize(rec_field, (0, 0), fx=scale, fy=scale)
    # cv2.imshow('Scaled receptive field map', disp)
    # cv2.waitKey(0)

if __name__ == '__main__':
    dat_file = os.path.abspath("C:\Users\Alex\PycharmProjects\heka_browser"
                               "\data\R2P_160817_04-jump_onds.dat")

    folder = [r'./jump_logs/on-ds']
    jump_logs = [r"C:\Users\Alex\PycharmProjects\StimulusProgram\psychopy"
                 r"\logs\2016_09_22\14h54m20s",
                 r"C:\Users\Alex\PycharmProjects\StimulusProgram\psychopy"
                 r"\logs\2016_09_22\14h54m27s"]

    kwargs = dict(dat_file=dat_file,
                  jump_logs=jump_logs,
                  group=1,
                  series=3,  # change according to file
                  # sweep=[1, 2, 3, 4, 5],
                  sweep=[1, 2],
                  # sweep=1,
                  data_trace=1,
                  trigger_trace=3,
                  thresh='2',
                  center_on='max',
                  # center_on='min',
                  window=0.75,
                  latency=10,
                  num_frames=3)

    img = main(**kwargs)
    # cv2.imshow('img', img)
    # cv2.waitKey(0)

    im = Image.fromarray(img)
    im.show()


