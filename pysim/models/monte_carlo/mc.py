import numpy as np


def create_matrix_1(p1, p2, p3, p4):
    '''Кумулятивная матрица для 1 сценария'''

    matrix = np.array([
        [1-p1, p1,  0, 0,  0],
        [1-p2, 0,  p2, 0,  0],
        [1-p3, 0,   0, p3, 0],
        [1-p4, 0,   0, 0,  p4],
        [0,    0,   0, 0,  1]
    ])
    return np.cumsum(matrix, axis=1)


def create_matrix_2(p1, p2, p3, p4):
    '''Кумулятивная матрица для 2 сценария'''

    matrix = np.array([
        [1-p1, p1,    0,    0,     0],
        [0,    1-p2,  p2,   0,     0],
        [0,    0,     1-p3, p3,    0],
        [0,    0,     0,    1-p4,  p4],
        [0,    0,     0,    0,     1]
    ])
    return np.cumsum(matrix, axis=1)


def create_matrix_3(probabilities):
    '''Кумулятивная матрица для 3 сценария'''
    n = len(probabilities) + 1
    matrix = np.zeros((n, n))

    for i in range(n-1):
        matrix[i][i] = 1 - probabilities[i]  # Элементы на главной диагонали
        matrix[i][i + 1] = probabilities[i]  # Элементы над главной диагональю

    matrix[n-1][n-1] = 1  # Последний элемент (поглощающее состояние)

    return np.cumsum(matrix, axis=1)


def create_input_probs(scenario, probs):
    '''
    Подготовить кумулятивные матрицы для
    запуска нескольких моделей Монте-Карло.

    Args:
        scenario: номемер сценария (1, 2, 3)
        probs: массив с массивами вероятностей перехода
        метки из одного состояния в другое
    '''

    matrix_list = []
    for i in range(len(probs)):
        if scenario == 1:
            matrix_list.append(create_matrix_1(*probs[i]))
        elif scenario == 2:
            matrix_list.append(create_matrix_2(*probs[i]))
        elif scenario == 3:
            matrix_list.append(create_matrix_3(probs[i]))
    return matrix_list


def run_multiple_models(scenario, probs, times, transmissions):
    matrix_list = create_input_probs(scenario, probs)
    res_time = []
    for i in range(len(probs)):
        res_time.append(monte_carlo(matrix_list[i], times[i], transmissions))

    return res_time


def monte_carlo(transition_matrix, stay_times, num_trials):
    num_states = len(transition_matrix)
    absorption_times = []

    for _ in range(num_trials):
        current_state = 0
        total_time = 0

        while current_state < num_states - 1:
            total_time += stay_times[current_state]
            rand_var = np.random.random()

            for index, elem in enumerate(transition_matrix[current_state]):
                if rand_var < elem:
                    current_state = index
                    break
        absorption_times.append(total_time)

    return sum(absorption_times)/len(absorption_times)*1000


if __name__ == '__main__':
    transmissions = 1_000
    t = (1, 2, 3, 4)
    matrix_2 = create_matrix_2(0.1, 0.1, 0.1, 0.1)
    res = monte_carlo(matrix_2, t, transmissions)
    print(f'Результат:\n{res}')
