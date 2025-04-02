import numpy as np


def convert_data_for_analitica(probs, t):
    '''
    Конвертация входных данных в формат,
    который требуют аналитические модели.
    '''
    all_phases = []
    sub_phase = []
    for cases in range(len(probs)):
        for state_number in range(len(probs[0])):
            sub_phase.append(
                (probs[cases][state_number], t[cases][state_number])
            )
        all_phases.append(sub_phase)
        sub_phase = []
    return all_phases


def calculate_first_case(phases):
    '''
    Расчёт для 1го сценария 1й версии аналитической модели.

    Args:
    phases: массив кортежей вида (p, t),
    где p - вероятность передачи,
    t - время нахождения в состоянии;
    '''
    times = [phase[1] for phase in phases]
    probs = [phase[0] for phase in phases]

    matrix = np.array([
        [probs[0],     -probs[0], 0,         0],
        [probs[1] - 1, 1,         -probs[1], 0],
        [probs[2] - 1, 0,         1,         -probs[2]],
        [probs[3] - 1, 0,         0,         1]
    ])

    return np.dot(np.linalg.inv(matrix)[0], np.array(times))


def calculate_second_case(phases):
    '''
    Расчёт для 2го сценария 1й версии аналитической модели.

    Args:
        phases: массив кортежей вида (p, t),
        где p - вероятность передачи,
        t - время нахождения в состоянии;
    '''
    res = 0
    for phase in phases:
        for n in range(1000):
            res += (n + 1) * phase[1] * phase[0] * ((1 - phase[0]) ** n)
    return res


def calculate_third_case(phases, chunk_phase, chunk_count):
    '''
    Расчёт для 3го сценария 1й версии аналитической модели.
    Данная модель предполагает, что времёна и вероятности перехода
    во всех состояниях Secured_R равны.

    Args:
        phases: массив кортежей вида (p, t),
        где p - вероятность передачи,
        t - время нахождения в состоянии;
        chunk_phase: кортеж вида (p, t) для
        всех состояний Secured_R;
        chunk_count: количество состояний Secured_R.
    '''
    return (
        calculate_second_case(phases) +
        chunk_count * calculate_second_case([chunk_phase])
    )


def run_analitica(script_number, all_phases, chunks_number):
    '''
    Последовательный запуск нескольких аналитических
    моделей для построения одной кривой графика.
    Распараллеливание в данном случае не применяется
    ввиду и так высокой скорости выполнения
    в последовательном режиме.
    '''
    analit_res = []
    if script_number == 1:
        for i in range(len(all_phases)):
            analit_res.append(calculate_first_case(all_phases[i])*1_000)
    elif script_number == 2:
        for i in range(len(all_phases)):
            analit_res.append(calculate_second_case(all_phases[i])*1_000)
    elif script_number == 3:
        for i in range(len(all_phases)):
            analit_res.append(
                calculate_third_case(
                    all_phases[i][0:3], all_phases[i][4], chunks_number
                )*1_000
            )
    return analit_res
