from engine.plugin import Plugin, PluginFactory, Registry

Registry.add_base('MapperOutput')
class MapperOutput(Plugin):

    def __init__(self, data, path=None):
        self.data = data
        self.path = path

    def process(self, *args, **kwargs):
        pass

    @classmethod
    def _register(cls, registry):
        registry[MapperOutput].add(cls)

    @classmethod
    def parse_context(cls, context):
        return cls(cls.parse_content(context.content), context.path)

    def parse_content(content):
        pass


class MapperOutputFactory(PluginFactory):

    def __init__(self):
        self.plugins = Registry.registry[MapperOutput]

    def create_plugin(self, P):
        pass


class A(MapperOutput):
    pass


class B(MapperOutput):
    a = A
    def process(self, local):
        self.log.info(self.a)
