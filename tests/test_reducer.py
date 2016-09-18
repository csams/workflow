from engine.plugin import Plugin, PluginFactory, reducer
from unittest import TestCase


class A(Plugin):
    pass


class B(Plugin):
    a = A

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


class TestRunPlugins(TestCase):

    def test_run_plugins(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
