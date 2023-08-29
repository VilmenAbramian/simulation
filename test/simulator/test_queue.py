from ._paths import eventQueue_dir
from pysim.sim import EventQueue
import pytest
    

def test_push_pop_single():
    queue = EventQueue()
    ev_id = queue.push(1, 'cat')

    assert len(queue) == 1
    assert (1, ev_id, 'cat') == queue.pop()
    assert len(queue) == 0

def test_pop():
    queue = EventQueue()
    queue.push(1, 'cat')        # 1
    queue.push(3, 'dog')        # 2
    queue.push(2, 'cow')        # 3
    queue.push(4, 'horse')      # 4
    queue.push(6, 'rooster')    # 5

    res = []
    res.append(queue.pop())
    res.append(queue.pop())
    res.append(queue.pop())
    res.append(queue.pop())
    res.append(queue.pop())

    assert res[0][2] == 'cat'
    assert res[1][2] == 'cow'
    assert res[2][2] == 'dog'
    assert res[3][2] == 'horse'
    assert res[4][2] == 'rooster'

# def test_void_queue_pop():
#     # TODO: Добавить проверку на вылет ошибки в случае пустой очереди   
#     pass

def test_cancel():
    queue = EventQueue()
    queue.push(1, 'cat')        # 0
    queue.push(3, 'dog')        # 1
    queue.push(2, 'cow')        # 2
    queue.push(4, 'horse')      # 3
    queue.push(6, 'rooster')    # 4
    queue.cancel(2)             # cow
    queue.cancel(4)             # rooster

    assert (1, 0, 'cat') == queue.pop()
    assert (3, 1, 'dog') == queue.pop()
    assert (4, 3, 'horse') == queue.pop()

    assert queue.empty
    with pytest.raises(KeyError):
        queue.pop()

def test_len():
    queue = EventQueue()
    queue.push(1, 'cat')        # 1
    queue.push(3, 'dog')        # 2
    queue.push(2, 'cow')        # 3
    queue.push(4, 'horse')      # 4
    queue.push(6, 'rooster')    # 5
    queue.cancel(0)
    queue.cancel(1)

    assert queue.__len__() == 3

    queue.cancel(3)
    assert queue.__len__() == 2

def test_clear():
    queue = EventQueue()
    queue.push(1, 'cat')        # 1
    queue.push(3, 'dog')        # 2
    queue.push(2, 'cow')        # 3
    queue.push(4, 'horse')      # 4
    queue.push(6, 'rooster')    # 5
    queue.clear()

    assert len(queue) != queue.empty

def test_cancel_not_existing():
    queue = EventQueue()
    queue.push(1, 'cat')        # 1
    queue.push(3, 'dog')        # 2
    queue.push(2, 'cow')        # 3
    queue.cancel(0)
    queue.cancel(0)
    queue.cancel(1000)

    assert (2, 2, 'cow') == queue.pop()
    assert (3, 1, 'dog') == queue.pop()
