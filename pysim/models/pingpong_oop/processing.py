import json
import time


def result_processing(initial_data, results, save_results = True):
    if save_results:
        current_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        filename = 'results/' + 'model_res-' + current_time + '.txt'
        with open(filename, 'w') as f:
            f.write(json.dumps(initial_data) + '\n')
            f.write(json.dumps(results.dict()))

    if isinstance(results, list):
        ...
    else:
        print('Результаты одиночного моделирования:')
        print(
            f'- Средний интервал отправки Ping клиентом (условные единицы) = {results.avg_interval}\n',
            f'- Средняя длительность передачи сообщения (условные единицы) = {results.avg_delay}\n',
            f'- Вероятность потери сообщения = {results.miss_rate}', sep=''
        )