from collections import defaultdict
from engine.plugin import Plugin, PluginFactory, Registry

class MapperOutputFactory(PluginFactory):

    __symbolic_map__ = defaultdict(set)
    ''' Map from target name to MapperOuput classes to process them. '''

    @classmethod
    def add_mapper(cls, name, plugin_class):
        cls.__symbolic_map__[name].append(plugin_class)

    def __init__(self, archive):
        self.plugins = Registry.registry[MapperOutput]
        self.archive = archive
        self.cur_context = None

    def run_order(self):
        pass

    def create_plugin(self, P):
        pass


Registry.add_base('MapperOutput')
class MapperOutput(Plugin):

    __target__ = None
    __filters__ = set()

    def __init__(self, data, path=None):
        self.data = data
        self.path = path

    def process(self, *args, **kwargs):
        pass

    @classmethod
    def _register(cls, registry):
        if cls.__target__:
            registry[MapperOutput].add(cls)
            MapperOutputFactory.add_mapper(cls.__target__, cls)

    @classmethod
    def parse_context(cls, context):
        return cls(cls.parse_content(context.content), context.path)

    @staticmethod
    def parse_content(content):
        pass
