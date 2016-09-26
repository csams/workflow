from engine.plugin import Plugin, PluginFactory, Registry
import unittest

Registry.add_base('MyPlugin')
class MyPlugin(Plugin):

    @classmethod
    def _register(cls, registry):
        registry[MyPlugin].add(cls)

class MyPluginFactory(PluginFactory):

    def __init__(self):
        self.plugins = Registry.registry[MyPlugin]

class A(MyPlugin):
    pass

class B(MyPlugin):
    a = A
    def process(self, local):
        self.log.info(self.a)

class TestMyFactory(unittest.TestCase):

    def test_myfactory(self):
        self.assertTrue(MyPlugin in Registry.registry)
        self.assertTrue(Registry.registry[MyPlugin] == set([A, B]))
