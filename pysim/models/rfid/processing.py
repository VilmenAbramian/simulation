import json
import matplotlib.pyplot as plt
from tabulate import tabulate
import time


def result_processing(initial_data, results, variadic, save_results=False):
    '''
    Обработка полученных данных из модели.
    Если была запущена только одна симуляция, то
    результаты выводятся в консоль. В противном случае
    данные можно сохранить в файл и построить по ним график.

    Если save_results = True, то входные и
    выходные данные сохраняются в .txt файл в
    папке results.
    '''
    if isinstance(results, tuple):
        # Результаты работы запуска одной симуляции
        print(tabulate([(key, value) for key, value in results[0].items()],
                        tablefmt='pretty'))
        print(f'Время выполнения симуляции: {results[1]} с.')
    elif isinstance(results, list):
        # Результаты работы запуска нескольких симуляций
        initial_data[variadic] = sorted(set(initial_data[variadic]))
        print_the_mult_results_to_the_terminal(initial_data, results, variadic)
        if save_results:
            save_mult_results_to_file(initial_data, results, variadic)
        plot_results(initial_data, results, variadic)


def separate_res(results):
    ret = []
    time_list = []
    for i in range(len(results)):
        ret.append(results[i][0])
        time_list.append(results[i][1])
    return ret, time_list


def results_to_dict(ret):
    results_dict = {'read_tid_prob': [], 'inventory_prob': [], 'rounds_per_tag':[]}
    for i in range(len(ret)):
        results_dict['read_tid_prob'].append(ret[i]['read_tid_prob'])
        results_dict['inventory_prob'].append(ret[i]['inventory_prob'])
        results_dict['rounds_per_tag'].append(ret[i]['rounds_per_tag'])
    return results_dict

def print_the_mult_results_to_the_terminal(initial_data, results, variadic):
    '''
    Результаты выводим в двух таблицах: таблице параметров и
    таблице результатов. В последней - значение изменяющегося аргумента
    и результаты, которые ему соответсвуют.
    '''
    params_names = [
        'speed', 'tid_word_size', 'altitude', 'reader_offset',
        'tag_offset', 'power', 'encoding', 'tari', 'num_tags']
    params_names.remove(variadic)

    ret, time_list = separate_res(results)

    print("\n# STATIC PARAMETERS:\n")
    print(tabulate([(name, initial_data[name]) for name in params_names],
                   tablefmt='pretty'))

    # Подготовим таблицу результатов.
    # Какие ключи нужны из словарей в списке ret (который вернул pool.map):
    ret_cols = ['read_tid_prob', 'inventory_prob', 'rounds_per_tag']
    # Строки таблицы результатов:
    results_table = [[item[column] for column in ret_cols] for item in ret]
    ret_cols.insert(0, variadic)
    for i in range(len(initial_data[variadic])):
        results_table[i].insert(0, initial_data[variadic][i])

    print("\n# RESULTS:\n")
    print(tabulate(results_table, headers=ret_cols, tablefmt='pretty'))
    print(f'Среднее время одной симуляции = {sum(time_list)/len(time_list)} с')


def save_mult_results_to_file(initial_data, results, variadic):
    current_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    filename = 'results/text/' + 'sim_res-' + current_time + '.txt'
    ret, time_list = separate_res(results)
    results_dict = results_to_dict(ret)
    with open(filename, 'w') as f:
        f.write('Входные параметры: ' + json.dumps(initial_data) + '\n')
        f.write('Результаты моделирования: ' + json.dumps(results_dict))

def plot_results(initial_data, results, variadic, save_fig = True):
    ret, _ = separate_res(results)
    results_dict = results_to_dict(ret)
    current_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    filename = 'results/plots/' + current_time + '-' + variadic + '.png'
    units = {'speed': 'km/h', 'reader_offset': 'm', 'altitude': 'm', 'power': 'dBm', 'tid_word_size': 'words'}
    
    fig, ax = plt.subplots(figsize=(14, 8), layout='constrained')
    ax.plot(
        initial_data[variadic], results_dict['read_tid_prob'],
        linewidth=3, linestyle='-',
        marker='s', markevery=30,
        markersize=8, label=initial_data['encoding'] + ', Tari = ' + initial_data['tari'] + ' µs'
    )
    ax.legend(fontsize=28)
    ax.set_ylabel('Probability of reading', fontsize=31)
    ax.set_xlabel(variadic + ', ' + units[variadic], fontsize=31)
    ax.tick_params(axis='both', which='major', labelsize=31)
    ax.grid()
    if save_fig:
        fig.savefig(filename)