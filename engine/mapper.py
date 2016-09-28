from collections import defaultdict
from engine.plugin import plugin, Plugin, PluginFactory, Registry


class MapperOutputFactory(PluginFactory):

    __symbolic_map__ = defaultdict(set)
    ''' Map from target name to MapperOuput classes to process them. '''

    __filter_map__ = defaultdict(set)
    ''' Map from target name to filters that should be applied to their contents. '''

    @classmethod
    def add_mapper(cls, name, plugin_class):
        if plugin_class.enabled:
            cls.__symbolic_map__[name].add(plugin_class)
            cls.__filter_map__[name] |= set(plugin_class.__filter_map__)

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

    @classmethod
    def _register(cls, registry):
        if cls.enabled and cls.__target__:
            registry[MapperOutput].add(cls)
            MapperOutputFactory.add_mapper(cls.__target__, cls)

    @classmethod
    def parse_context(cls, context):
        return cls(cls.parse_content(context.content), context.path)

    @staticmethod
    def parse_content(content):
        pass


def mapper(target, filters=set(), enabled=True):
    ''' Syntactic sugar to create a MapperOutput class. '''

    def _wrap(thing):
        try:
            if issubclass(thing, MapperOutput):
                thing.__target__ = target
                thing.__filters__ = filters
                thing.enabled = enabled
                MapperOutputFactory.add_mapper(target, thing)
            else:
                raise Exception('%s is not a MapperOutput subclass.' % thing)
        except:
            attrs = {
                '__target__': target,
                '__filters__': filters
            }
            return plugin(kind=MapperOutput, enabled=enabled, attrs=attrs)
    return _wrap 
