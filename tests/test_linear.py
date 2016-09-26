from engine.plugin import Plugin, PluginFactory
from unittest import TestCase

class A(Plugin):
    def process(self, local):
        pass

class B(Plugin):
    a = A
    def process(self, local):
        pass

class TestRunPlugins(TestCase):

    def test_linear(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(graph[B].a is not None)
