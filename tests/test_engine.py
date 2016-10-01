from unittest import TestCase
from engine import run_order

from engine.reducer import reducer, Reducers

@reducer()
def reportA(local, shared):
    pass

@reducer(requires=[reportA])
def reportB(local, shared):
    pass

@reducer(requires=[reportB, reportA])
def reportC(local, shared):
    pass

class TestOrder(TestCase):

    def test_order(self):
        ordered = run_order(Reducers.from_module(self.__module__))
        self.assertTrue(ordered.index(reportA) < ordered.index(reportB))
        self.assertTrue(ordered.index(reportB) < ordered.index(reportC))
