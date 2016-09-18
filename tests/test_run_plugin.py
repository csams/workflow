from engine.plugin import Dep, Plugin, PluginFactory
from unittest import TestCase


class A(Plugin):
    pass


class B(Plugin):
    a = Dep(A)

    def process(self):
        self.log.info(self.a)


class C(Plugin):
    a = Dep(A)
    b = Dep(B)

    def process(self):
        self.log.info(self.a)
        self.log.info(self.b)


class D(Plugin):
    a = Dep(A, optional=True)
    c = Dep(C, optional=True)

    def process(self):
        self.log.info(self.a)
        self.log.info(self.c)


class E(Plugin):
    d = Dep(D)

    def process(self):
        self.log.info(self.d)


class TestRunPlugins(TestCase):

    def test_run_plugins(self):
        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
