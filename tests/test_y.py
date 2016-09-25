from engine.plugin import Plugin, PluginFactory
from unittest import TestCase

class A(Plugin):
    def process(self):
        pass

class B(Plugin):
    def process(self):
        pass

class C(Plugin):
    a = A
    b = B
    def process(self):
        pass

class TestRunPlugins(TestCase):

    def test_hat(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(graph[C].a is not None)
        self.assertTrue(graph[C].b is not None)
