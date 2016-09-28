from engine.reducer import reducer, Reducer, ReducerFactory
from unittest import TestCase


class A(Reducer):
    pass


class B(Reducer):
    a = A

    def process(self, local):
        self.log.info(self.a)

class C(Reducer):
    enabled = False

    def process(self, local):
        self.log.info(self.a)


@reducer(requires=[A])
def redc(shared, local):
    shared.log.info(shared.a)
    shared.thing = 4


@reducer(requires=[redc, B])
def red(shared, local):
    shared.log.info(shared.redc.thing)
    shared.log.info(shared.b)


@reducer(requires=[[B, C]])
def D(shared, local):
    shared.log.info(shared.b)
    shared.log.info(shared.c)


class TestRunPlugins(TestCase):

    def test_reducer(self):
        graph = ReducerFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))

    def test_any(self):
        graph = ReducerFactory().run_plugins()
        self.assertTrue(D in graph)
        self.assertTrue(graph[D].b is not None)
        self.assertTrue(graph[D].c is None)
