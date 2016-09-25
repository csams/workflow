from engine.plugin import Any, All, Plugin, PluginFactory
from unittest import TestCase


class A(Plugin):
    pass


class B(Plugin):
    a = A

    def process(self):
        self.log.info(self.a)


class C(Plugin):
    enabled = False
    a = A

    def process(self):
        self.log.info(self.a)

class D(Plugin):
    enabled = False

    def process(self):
        self.log.info(self.a)


class E(Plugin):
    __policies__ = [Any(a=A, c=C)]

    def process(self):
        self.log.info(self.a)
        self.log.info(self.c)

class F(Plugin):
    __policies__ = [Any(c=C, d=D)]

    def process(self):
        self.log.info(self.c)
        self.log.info(self.d)

class G(Plugin):
    __policies__ = [All(a=A, b=B)]

    def process(self):
        self.log.info(self.a)
        self.log.info(self.b)

class H(Plugin):
    __policies__ = [All(a=A, c=C)]

    def process(self):
        self.log.info(self.a)
        self.log.info(self.c)


class TestRunPlugins(TestCase):

    def test_any(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(graph[E].a is not None)
        self.assertTrue(graph[E].c is None)

    def test_not_any(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(F not in graph)

    def test_all(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(G in graph)

    def test_not_all(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        self.assertTrue(H not in graph)
