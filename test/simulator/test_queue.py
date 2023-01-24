from pysim.sim import EventQueue
import pytest
    

def test_push():
    queue = EventQueue()
    queue.push(1, 'event')
    assert not queue.empty and queue.__len__() == 1

def test_pop():
    queue = EventQueue()
    queue.push(2, 'event_0')
    queue.push(4.5, 'event_1')
    queue.push(3, 'event_2')
    queue.push(1, 'event_3')
    queue.push(3, 'event_4')
    res = []
    while queue.__len__() != 0:
        res.append(queue.pop())
    assert res[0][0]<=res[1][0]<=res[2][0]<=res[3][0]<=res[4][0] and res[2][1] < res[3][1]


# def test_void_queue_pop():
#     # TODO: Добавить проверку на вылет ошибки в случае пустой очереди   
#     pass

def test_cancel():
    queue = EventQueue()
    id_list = []
    for i in range(10):
        id_list.append(queue.push(i, 'event')) 
    queue.cancel(id_list[2])
    assert queue.__len__() == 9
    queue.cancel(id_list[2])
    assert queue.__len__() == 9

def test_len():
    queue = EventQueue()
    for i in range(10):
        queue.push(i, 'event')
    assert queue.__len__() == 10
    queue.cancel(0)
    queue.cancel(1)
    assert queue.__len__() == 8
    queue.cancel(1)
    assert queue.__len__() == 8
    queue.push(15, 'new_event')
    assert queue.__len__() == 9

def test_clear():
    queue = EventQueue()
    for i in range(10):
        queue.push(i, 'event')
    queue.clear()
    assert queue.__len__() != queue.empty