from pysim.sim import EventQueue
import pytest

# def test_push():
#     event = EventQueue()
#     event_number = EventQueue.push(event, 1, "event")
    

# def test_pop():
#     pass
# def test_cansel():
#     pass

def test_len():
    event = EventQueue()
    for i in range(10):
        EventQueue.push(event, i, 'event')
    assert EventQueue.__len__(event) == 10