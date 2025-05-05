import json
import os
import matplotlib.pyplot as plt
import time


def result_processing(kwargs, result, save_res=True, plot_res=False):
    if (len(kwargs['probability']) > 1 and
           (type(kwargs['probability'][0]) is tuple)):
        res = []
        for i in result:
            res.append(i.sim_time/kwargs['max_transmisions'])
        print('Среднее время до поглощения: ', res)
        if save_res:
            save_results(kwargs, res)
        if plot_res:
            plot_results(kwargs, res)
    else:
        print('Суммарное время: ', result.sim_time)
        print('Среднее время до поглощения: ',
              result.sim_time/kwargs['max_transmisions'])


def save_results(kwargs, res):
    current_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    filename = 'results/text/' + 'sim_res-' + current_time + '.txt'
    with open(filename, 'w') as f:
        f.write('Входные параметры: ' + json.dumps(kwargs) + '\n')
        f.write('Результаты моделирования: ' + json.dumps(res))


def plot_results(kwargs, res, save_fig=True):
    current_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    filename = 'results/plots/' + current_time + '.png'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 8), layout='constrained')
    ax.plot(
        list(range(len(kwargs['probability']))), res,
        linewidth=3, linestyle='-',
        marker='s', markevery=30,
        markersize=8,
    )
    if save_fig:
        fig.savefig(filename)
