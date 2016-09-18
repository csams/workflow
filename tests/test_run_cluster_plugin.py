import logging
from engine.plugin import Dep, Plugin, ClusterPlugin, PluginFactory, ClusterPluginFactory, reducer
from unittest import TestCase

log = logging.getLogger(__name__)


class A(Plugin):
    pass


class B(Plugin):
    a = A

    def process(self):
        self.log.info(self.a)


class C(Plugin):
    a = A
    b = B

    def process(self):
        self.log.info(self.a)
        self.log.info(self.b)


class D(Plugin):
    a = Dep(A, optional=True)
    b = Dep(B, on_error=True)
    c = Dep(C, optional=True)

    def process(self):
        self.log.info(self.a)
        self.log.info(self.c)


class E(Plugin):
    d = D

    def process(self):
        self.log.info(self.d)


@reducer(kind=ClusterPlugin)
def reduceA(shared):
    log.info(shared)


@reducer(requires=[reduceA], kind=ClusterPlugin)
def reduceB(shared):
    log.info(shared)


class TestRunPlugins(TestCase):

    def test_run_plugins(self):
        # the idea here is for cluster archives.  A subclass
        # of PluginFactory that will create the appropriate plugins
        # based on file availability will be created for each archive
        # in the cluster archive, and the graph of each run_plugins
        # call for those archives will be accumulated and passed
        # to the ClusterPluginFactory, which will run the ClusterPlugins
        # each PluginFactory graph is a dictionary of the form
        # {PluginClass: PluginClass instance(s)}

        graph = PluginFactory().run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
        graphs = {'some_role?': graph}
        graph = ClusterPluginFactory(graphs).run_plugins()
        self.assertTrue(not any(p._exception for p in graph.values()))
