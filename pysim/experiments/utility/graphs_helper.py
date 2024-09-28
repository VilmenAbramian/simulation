from itertools import product
import math # Для работы аналитической модели
import numpy as np
from pprint import pprint

# Подключение старые пакеты для моделирования протокола RFID
from pysim.models.monte_carlo.protocol import (TagFrame, ReaderFrame, TagEncoding,
    Sel, DR, Session, Bank, InventoryFlag as Flag,
    Query, QueryRep, Ack, ReqRn, Read,
    Rn16Reply, AckReply, ReqRnReply, ReadReply, max_t1, max_t2)

# Подключение имитационок для аналитики
from pysim.models.monte_carlo.cli import create_config, run_multiple_simulation


def random_hex_string(bs: int) -> str:
    '''
    Функция для генерации случайного EPC и TID
    '''
    return "".join([f"{np.random.randint(0, 256):02X}" for _ in range(bs)])

Q = 4             # по-умолчанию, будем исходить из этого значения параметра Q
RTCAL_MUL = 2.75  # во сколько раз RTcal больше Tari
TRCAL_MUL = 1.95  # во сколько раз TRcal больше RTcal
EPC_SIZE = 12     # длина EPCID в байтах
TID_SIZE = 8      # длина TID в байтах
EPC = random_hex_string(EPC_SIZE)
TID = random_hex_string(TID_SIZE)

def calculate_chunks(words_number: int, chunks_number: int) -> tuple[int, int]:
    '''
    Рассчитывает количество 'чанков' и длину последнего
    Возвращает tuple:
      words_number_in_one_chunk - количество слов во всех 'чанках', крооме последнего
      last_chunk_len - количество слов в последнем чанке. Если 'чанк' всего один, то
      last_chunk_len = 0
    '''
    words_number_in_one_chunk = words_number
    last_chunk_len = 0
    number_chunks_to_send = chunks_number
    if chunks_number > 1:
        words_number_in_one_chunk = words_number // chunks_number
        last_chunk_len = words_number // chunks_number + words_number % chunks_number
    # print(f'Слов в одном чанке: {words_number_in_one_chunk}')
    # print(f'Слов в последнем чанке: {last_chunk_len}')
    return words_number_in_one_chunk, last_chunk_len


def build_messages_df(tari_us, m, drs, trext, chunks_number, words_number_in_one_chunk, last_chunk_len):
    """
    Построить DataFrame для всевозможных настроек канала и рассчитанными 
    длительностями команд и ответов.
    
    В датафрейме используются следующие единицы измерений:
    
    - для длительностей: микросекунды (мкс)
    - для частот: килогерцы (КГц)
    - для скоростей: килобиты в секунду (кбит/с)
    
    Returns:
        df (DataFrame)
    """
    params = []
    for tari_us, m, dr, trext in product(tari_us, m, drs, trext):
        tari = tari_us * 1e-6
        rtcal = RTCAL_MUL * tari
        trcal = TRCAL_MUL * rtcal
        blf = dr.ratio / trcal
        bitrate = blf / m.value
        
        # Строим команды
        # --------------
        preamble = ReaderFrame.Preamble(tari, rtcal, trcal)
        sync = ReaderFrame.Sync(tari, rtcal)
        
        query = Query(dr=dr, m=m, trext=trext, sel=Sel.SL_ALL, 
                           session=Session.S0, target=Flag.A, 
                           q=Q, crc5=0x15)
        query_rep = QueryRep(session=Session.S0)
        ack = Ack(0x5555)
        req_rn = ReqRn(0x5555, 0x5555)
        read = Read(Bank.TID, 0, 4, rn=0x5555, crc16=0x5555)
        
        # Строим ответы
        # -------------
        rn16 = Rn16Reply(0x5555)
        epc_pc = AckReply(EPC)
        handle = ReqRnReply(0)
        data = []
        # Для 3го сценария создаём несколько ответов для каждого 'чанка'
        if chunks_number > 1:
            for i in range(chunks_number-1):
                data.append(ReadReply([0xABAB] * words_number_in_one_chunk, 0, 0))
            data.append(ReadReply([0xABAB] * last_chunk_len, 0, 0))
        else:
            data = [ReadReply([0xABAB] * words_number_in_one_chunk, 0, 0)]
        data_durations = []
        data_lens = []
        for data_answer in data:
            data_durations.append(TagFrame(m, trext, blf, data_answer).duration)
            data_lens.append(TagFrame(m, trext, blf, data_answer).bitlen)

        params.append({
            'DR': dr,
            'M': m,
            'Tari': tari_us,     
            'TRext': trext,
            'RTcal': rtcal,
            'TRcal': trcal,
            'BLF': blf,
            'Query': ReaderFrame(preamble, query).duration,
            'QueryRep': ReaderFrame(sync, query_rep).duration,
            'Ack': ReaderFrame(sync, ack).duration,
            'Req_RN': ReaderFrame(sync, req_rn).duration,
            'Read': ReaderFrame(sync, read).duration,
            'Query_len': 22,
            'RN16': TagFrame(m, trext, blf, rn16).duration,
            'EPC+PC+CRC': TagFrame(m, trext, blf, epc_pc).duration,
            'Handle': TagFrame(m, trext, blf, handle).duration,
            'Data': data_durations,
            'RN16_len': TagFrame(m, trext, blf, rn16).bitlen,
            'EPC+PC+CRC_len': TagFrame(m, trext, blf, epc_pc).bitlen,
            'Handle_len': TagFrame(m, trext, blf, handle).bitlen,
            'Data_len': data_lens,
        })
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
        params[0]['RN16_len'],
        params[0]['EPC+PC+CRC_len'],
        params[0]['Handle_len'],
    ]
    for i in range(chunks_number):
        reply_lens.append(params[0]['Data_len'][i])
    
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
    T1 = max_t1(params[0]['RTcal'], params[0]['BLF'])
    T2 = max_t2(params[0]['BLF'])
    T1_2 = T1 + T2
    delta = 1e-5
    
    times = []
    T_arbitrate = T1_2 + params[0]['Query'] + params[0]['RN16'] + 2 * delta
    times.append(T_arbitrate)
    T_reply = T1_2 + params[0]['Ack'] + params[0]['EPC+PC+CRC'] + 2 * delta
    times.append(T_reply)
    T_acknowledged = T1_2 + params[0]['Req_RN'] + params[0]['Handle'] + 2 * delta
    times.append(T_acknowledged)
    
    for i in range(chunks_number):
        t_chunk = T1_2 + params[0]['Read'] + params[0]['Data'][i] + 2 * delta
        times.append(t_chunk)
    
    # Копирование массивов времени по количеству
    # массивов вероятности
    t = []
    for _ in range(len(probs)):
        t.append(times)
    return t


# Подготовка словарей для запуска имитационок
# Словарь для запуска одной имитационки:
def create_dicts(probabilities, times, chunks_number, scenario, max_transmissions):
    '''
    Готовит словарь для запуска нескольких имитационок параллельно
    '''
    return {
        'probability': probabilities,
        'processing_time': times,
        'max_transmisions': max_transmissions,
        'chunks_number': chunks_number,
        'scenario': scenario
    }

def run_set_simulations(start_dict):
    return run_multiple_simulation(start_dict)


# phases is array of tuples (p, t), where p is transmission prob, t is timeout time
def calculate_first_case(phases):
    res = 0;
    times = [phase[1] for phase in phases]
    probs = [phase[0] for phase in phases]
    
    for n1 in range(40):
        for n2 in range(40):
            for n3 in range(40):
                for n4 in range(40):
                    t = times[0] + times[1] + times[2] + times[3] + (n1 + n2+ n3 + n4) * times[0] + (n2 + n3 + n4) * times[1] + (n3 + n4) * times[2] + n4 * times[3]
                    p = ((1 - probs[0]) ** n1) * (probs[0] ** (n2 + n3 + n4 + 1)) * ((1 - probs[1]) ** n2) * (probs[1] ** (n3 + n4 + 1)) * ((1 - probs[2]) ** n3) * (probs[2] ** (n4 + 1)) * ((1 - probs[3]) ** n4) * probs[3]
                    fact = math.factorial(n1 + n2 + n3 + n4) / (math.factorial(n1) * math.factorial(n2) * math.factorial(n3) * math.factorial(n4))
                    res += t * p * fact

    return res


# phases is array of tuples (p, t), where p is transmission prob, t is timeout time
def calculate_second_case(phases):
    res = 0

    for phase in phases:
        for n in range(1000):
            res += (n + 1) * phase[1] * phase[0] * ((1 - phase[0]) ** n)

    return res


def calculate_third_case(phases, chunk_phase, chunk_count):
    return calculate_second_case(phases) + chunk_count * calculate_second_case([chunk_phase])


# Коневертация данных в формат, который требуют аналитические модели
def convert_data_for_analitica(probs, t):
    all_phases = []
    sub_phase = []
    for cases in range(len(probs)):
        for state_number in range(len(probs[0])):
            sub_phase.append((probs[cases][state_number], t[cases][state_number]))
        all_phases.append(sub_phase)
        sub_phase = []
    return all_phases


def run_analitica(script_number, all_phases):
    analit_res = []
    if script_number == 1:
        for i in range(len(all_phases)):
            analit_res.append(calculate_first_case(all_phases[i])*1_000)
    elif script_number == 2:
        for i in range(len(all_phases)):
            analit_res.append(calculate_second_case(all_phases[i])*1_000)
    elif script_number == 3:
        for i in range(3):
            analit_res.append(calculate_third_case(all_phases[i], all_phases[-1], CHUNKS_NUMBER)*1_000)
    return analit_res