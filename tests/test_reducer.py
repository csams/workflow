from engine.plugin import Plugin, PluginFactory, reducer
from unittest import TestCase


class A(Plugin):
    pass


class B(Plugin):
    a = A

    def process(self):
        self.log.info(self.a)

class C(Plugin):
    enabled = False

    def process(self):
        self.log.info(self.a)


@reducer(requires=[A])
def redc(shared):
    shared.log.info(shared.a)
    shared.thing = 4


@reducer(requires=[redc, B])
def red(shared):
    shared.log.info(shared.redc.thing)
    shared.log.info(shared.b)


@reducer(requires=[[B, C]])
def D(shared):
    shared.log.info(shared.b)


#@reducer(requires=[C])
#def E(shared):
#    shared.log.info(shared.b)


class TestRunPlugins(TestCase):

    def test_reducer(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))

    def test_any(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(D in graph)
        self.assertTrue(graph[D].b is not None)
        self.assertTrue(graph[D].c is None)

