from engine.plugin import plugin, ClusterPlugin, ClusterPluginFactory, Plugin, PluginFactory, Registry

class ReducerFactory(PluginFactory):

    def __init__(self):
        self.plugins = Registry.registry[Reducer]


Registry.add_base('Reducer')
class Reducer(Plugin):

    def process(self, *args, **kwargs):
        pass

    @classmethod
    def _register(cls, registry):
        registry[Reducer].add(cls)


class ClusterReducerFactory(ClusterPluginFactory):

    def __init__(self, graphs):
        self.graphs = graphs
        self.plugins = Registry.registry[ClusterReducer]


Registry.add_base('ClusterReducer')
class ClusterReducer(ClusterPlugin):

    @classmethod
    def _register(cls, registry):
        registry[ClusterReducer].add(cls)


def reducer(requires=[], optional=[], cluster=False, enabled=True):
    kind = Reducer if not cluster else ClusterReducer
    return plugin(requires=requires, optional=optional, kind=kind, enabled=enabled)
