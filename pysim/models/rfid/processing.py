import json
from tabulate import tabulate
import time


def result_processing(initial_data, results, variadic, save_results=False):
    '''
    Обработка полученных данных из модели.
    Если была запущена только одна симуляция, то
    результаты выводятся в консоль. В противном случае
    данные можно сохранить в файл или построить по ним график.

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
        print('initial_data: ', initial_data)
        print('results: ', results)
        print('variadic: ', variadic)




    # result['encoding'] = encoding.name
    # result['tari'] = f"{tari * 1e6:.2f}"
    # result['speed'] = speed
    # result['tid_word_size'] = tid_word_size
    # result['reader_offset'] = reader_offset
    # result['tag_offset'] = tag_offset
    # result['altitude'] = altitude
    # result['power'] = power
      
      
#         # Результаты выводим в двух таблицах: таблице параметров и
#         # таблице результатов. В последней - значение изменяющегося аргумента
#         # и результаты, которые ему соответсвуют.
#         params_names = list(var_arg_names) + ["encoding", "tari", "num_tags"]
#         params_names.remove(variadic)

#         print("\n# PARAMETERS:\n")
#         print(tabulate([(name, kwargs[name]) for name in params_names],
#                        tablefmt='pretty'))

#         # Подготовим таблицу результатов.
#         # Какие ключи нужны из словарей в списке ret (который вернул pool.map):
#         # FIXME: ошибка в добавлении столбца с изменяющимся параметром
#         # ret_cols = (variadic, "read_tid_prob", "inventory_prob",
#         #             "rounds_per_tag")
#         ret_cols = ("read_tid_prob", "inventory_prob",
#                     "rounds_per_tag")
#         print('ret_cols :', ret_cols)
#         print('ret: ', ret)
#         # Строки таблицы результатов:
#         results_table = [[item[column] for column in ret_cols] for item in ret]
#         print("\n# RESULTS:\n")
#         print(tabulate(results_table, headers=ret_cols, tablefmt='pretty'))