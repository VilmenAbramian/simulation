import numpy as np
from pprint import pprint

import pysim.models.rfid.epcstd as p2

# Подключение имитационок
from pysim.models.monte_carlo.cli import run_multiple_simulation

# ----------------------------------------------------
# Задать константы для работы моделей
# ----------------------------------------------------

def random_hex_string(bs: int) -> str:
    '''
    Генерация случайных EPC и TID
    '''
    return ''.join([f'{np.random.randint(0, 256):02X}' for _ in range(bs)])

Q = 4             # по-умолчанию, будем исходить из этого значения параметра Q
RTCAL_MUL = 2.75  # во сколько раз RTcal больше Tari
TRCAL_MUL = 1.95  # во сколько раз TRcal больше RTcal
EPC_SIZE = 12     # длина EPCID в байтах
TID_SIZE = 8      # длина TID в байтах
EPC = random_hex_string(EPC_SIZE)
TID = random_hex_string(TID_SIZE)

# Константы для флагов
SESSION_FLAG = p2.Session.S0
INVENTORY_FLAG = p2.InventoryFlag.A
SELECT_FLAG = p2.SelFlag.ALL

# ----------------------------------------------------
# Подготовка входных параметров в модели
# ----------------------------------------------------

def calculate_chunks(words_number: int, chunks_number: int) -> tuple[int, int]:
    '''
    Рассчитывает количество 'чанков' и длину последнего 'чанка'

    Args:
        words_number: суммарное количество передаваемых меткой
        слов (16 бит) в состоянии Read;
        chunks_number: количество 'чанков' (фрагментов), на которые
        будет разбито сообщение длиной words_number. Для 1-го и 
        2-го сценариев равно 1.

    Returns:
        words_number_in_one_chunk: количество слов во всех 'чанках', крооме последнего;
        last_chunk_len: количество слов в последнем чанке. Если 'чанк' всего один, то
        last_chunk_len = 0.
    '''
    words_number_in_one_chunk = words_number
    last_chunk_len = 0
    if chunks_number > 1:
        words_number_in_one_chunk = words_number // chunks_number
        last_chunk_len = words_number // chunks_number + words_number % chunks_number
    # print(f'Слов в одном чанке: {words_number_in_one_chunk}')
    # print(f'Слов в последнем чанке: {last_chunk_len}')
    return words_number_in_one_chunk, last_chunk_len


def create_commands(tari, rtcal, trcal, dr, m, trext) -> dict:
    '''
    Создать команды RFID считывателя
    '''
    commands = {}
    commands['preamble'] = p2.ReaderPreamble(tari, rtcal, trcal)
    commands['sync'] = p2.ReaderSync(tari, rtcal)
    commands['query'] = p2.Query(dr=dr, m=m, trext=trext, sel=SELECT_FLAG, 
                        session=SESSION_FLAG, target=INVENTORY_FLAG, 
                        q=Q, crc=0x15)
    commands['query_rep'] = p2.QueryRep(session=SESSION_FLAG)
    commands['ack'] = p2.Ack(0x5555)
    commands['req_rn'] = p2.ReqRN(0x5555, 0x5555)
    commands['read'] = p2.Read(p2.MemoryBank.TID, 0, 4, rn=0x5555, crc=0x5555)

    return commands


def create_replies(m, trext, chunks_number, words_number_in_one_chunk, last_chunk_len) -> dict:
    '''
    Создать ответы RFID метки
    '''
    replies = {}
    replies['tag_preamble'] = p2.create_tag_preamble(encoding = m, extended = trext)
    replies['rn16'] = p2.QueryReply(0x5555)
    replies['epc_pc'] = p2.AckReply(EPC)
    replies['handle'] = p2.ReqRNReply(0)
    data = []
    # Для 3го сценария создаём несколько ответов для каждого 'чанка'
    if chunks_number > 1:
        for _ in range(chunks_number-1):
            data.append(p2.ReadReply('ABAB' * words_number_in_one_chunk))
        data.append(p2.ReadReply('ABAB' * last_chunk_len))
    else:
        data = [p2.ReadReply('ABAB' * words_number_in_one_chunk)]
    replies['data'] = data

    return replies


def build_messages_df(tari_us, m, dr, trext, chunks_number, words_number_in_one_chunk, last_chunk_len) -> dict:
    """
    Создать RFID сообщения для расчёта их длины (в битах) и длительности (в мкс)

    Args:
        chunks_number: количество 'чанков' (фрагментов), на которые
        будет разбито сообщение длиной words_number. Для 1-го и 
        2-го сценариев равно 1;
        words_number_in_one_chunk: количество слов в одном чанке;
        last_chunk_len: количество слов в последнем чанке.

    """
    tari = tari_us * 1e-6
    rtcal = RTCAL_MUL * tari
    trcal = TRCAL_MUL * rtcal
    blf = dr.eval() / trcal
    
    # Строим команды
    commands = create_commands(tari, rtcal, trcal, dr, m, trext)
    sync = commands['sync']
    
    # Строим ответы
    replies = create_replies(m, trext, chunks_number, words_number_in_one_chunk, last_chunk_len)
    tag_preamble = replies['tag_preamble']

    # Длительность (мкс) и длина (биты) ответа на комаду Read
    data_durations = []
    data_lens = []
    for data_answer in replies['data']:
        data_durations.append(p2.TagFrame(tag_preamble, data_answer).get_duration(blf))
        data_lens.append(p2.TagFrame(tag_preamble, data_answer).bitlen)

    params = {
        'DR': dr,
        'M': m,
        'Tari': tari_us,     
        'TRext': trext,
        'RTcal': rtcal,
        'TRcal': trcal,
        'BLF': blf,
        'Query': p2.ReaderFrame(commands['preamble'], commands['query']).duration,
        'QueryRep': p2.ReaderFrame(sync, commands['query_rep']).duration,
        'Ack': p2.ReaderFrame(sync, commands['ack']).duration,
        'Req_RN': p2.ReaderFrame(sync, commands['req_rn']).duration,
        'Read': p2.ReaderFrame(sync, commands['read']).duration,
        'Query_len': 22,
    
        'RN16': p2.TagFrame(tag_preamble, replies['rn16']).get_duration(blf),
        'EPC+PC+CRC': p2.TagFrame(tag_preamble, replies['epc_pc']).get_duration(blf),
        'Handle': p2.TagFrame(tag_preamble, replies['handle']).get_duration(blf),
        'Data': data_durations,

        'RN16_len': p2.TagFrame(tag_preamble, replies['rn16']).bitlen,
        'EPC+PC+CRC_len': p2.TagFrame(tag_preamble, replies['epc_pc']).bitlen,
        'Handle_len': p2.TagFrame(tag_preamble, replies['handle']).bitlen,
        'Data_len': data_lens,

        'rtcal': rtcal,
        'trcal': trcal,

    }
    return params


def prepare_probs(params, chunks_number, ber, points_number):
    '''
    Пересчитывает ber во входные параметры вероятности 
    для моделей
    Группирует вероятности по массивам:
    [
      [Массив вероятностей 1], ..., [Массив вероятностей n]
    ]
    '''
    reply_lens = [
        params['RN16_len'],
        params['EPC+PC+CRC_len'],
        params['Handle_len'],
    ]
    for i in range(chunks_number):
        reply_lens.append(params['Data_len'][i])
    
    probabilities = []
    for i in range(len(reply_lens)):
        probabilities.append((1 - ber) ** reply_lens[i]) 

    probs = []
    sub_probabilities = []
    for i in range(points_number):
        for state_number in range(len(reply_lens)):
            sub_probabilities.append(probabilities[state_number][i])
        probs.append(sub_probabilities)
        sub_probabilities = []
    return probs


def prepare_times(params, probs, chunks_number):
    # FIXME: Добавить передачу DR из словаря params
    T1 = p2.link_t1_max(rtcal=params['rtcal'], trcal=params['trcal'], dr=None)
    T2 = p2.link_t2_max(trcal=params['trcal'], dr=None)
    T1_2 = T1 + T2
    delta = 1e-5
    
    times = []
    T_arbitrate = T1_2 + params['Query'] + params['RN16'] + 2 * delta
    times.append(T_arbitrate)
    T_reply = T1_2 + params['Ack'] + params['EPC+PC+CRC'] + 2 * delta
    times.append(T_reply)
    T_acknowledged = T1_2 + params['Req_RN'] + params['Handle'] + 2 * delta
    times.append(T_acknowledged)
    
    for i in range(chunks_number):
        t_chunk = T1_2 + params['Read'] + params['Data'][i] + 2 * delta
        times.append(t_chunk)
    
    # Копирование массивов времени по количеству
    # массивов вероятности
    t = []
    for _ in range(len(probs)):
        t.append(times)
    return t


def create_dicts(probabilities, times, chunks_number, scenario, max_transmissions):
    '''
    Подготовка словаря для запуска нескольких имитационок параллельно
    '''
    return {
        'probability': probabilities,
        'processing_time': times,
        'max_transmisions': max_transmissions,
        'chunks_number': chunks_number,
        'scenario': scenario
    }

# ----------------------------------------------------
# Запуск имитационных моделей
# ----------------------------------------------------

def run_set_simulations(start_dict):
    '''
    Параллельный запуск нескольких имитационных
    моделей для построения одной кривой графика.
    '''
    return run_multiple_simulation(start_dict)

# ----------------------------------------------------
# Подготовка и запуск аналитических
# моделей для расчёта времени
# ----------------------------------------------------

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
        [probs[0]    , -probs[0], 0        , 0        ],
        [probs[1] - 1, 1        , -probs[1], 0        ],
        [probs[2] - 1, 0        , 1        , -probs[2]],
        [probs[3] - 1, 0        , 0        , 1        ]
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
    return calculate_second_case(phases) + chunk_count * calculate_second_case([chunk_phase])


def convert_data_for_analitica(probs, t):
    '''
    Конвертация входных данных в формат,
    который требуют аналитические модели.
    '''
    all_phases = []
    sub_phase = []
    for cases in range(len(probs)):
        for state_number in range(len(probs[0])):
            sub_phase.append((probs[cases][state_number], t[cases][state_number]))
        all_phases.append(sub_phase)
        sub_phase = []
    return all_phases


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
            analit_res.append(calculate_third_case(all_phases[i][0:3], all_phases[i][4], chunks_number)*1_000)
    return analit_res