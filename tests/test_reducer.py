from unittest import TestCase

from engine.reducer import reducer, Reducers

@reducer()
def reducerA(local, shared):
    return 3

@reducer(requires=[reducerA])
def reducerB(local, shared):
    return shared.reducera

class TestDependencies(TestCase):

    def test_registration(self):
        self.assertTrue(reducerA in Reducers.all())
        self.assertTrue(reducerB in Reducers.all())

    def test_depends(self):
        self.assertTrue(reducerA in reducerB.depends)
