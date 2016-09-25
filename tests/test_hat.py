from engine.plugin import Plugin, PluginFactory
from unittest import TestCase

class A(Plugin):
    def process(self):
        pass

class B(Plugin):
    a = A
    def process(self):
        pass

class C(Plugin):
    a = A
    def process(self):
        pass

class TestRunPlugins(TestCase):

    def test_hat(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(graph[B].a is not None)
        self.assertTrue(graph[C].a is not None)
