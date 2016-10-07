import collections
from engine.registry import Plugin, Registry, wrap


Registry.add_base('MapperOutput')
class MapperOutput(Plugin):
    mappers_by_symbol = collections.defaultdict(set)
    symbols_by_mapper = collections.defaultdict(set)
    filters = collections.defaultdict(set)
    
    @classmethod
    def register(cls, registry):
        registry.add_plugin(MapperOutput, cls)
                
    def __init__(self, data, path=None):
        self.data = data
        self.path = path
        self._exception = None

    # a few mapper specific registry methods
    @classmethod
    def for_symbol(cls, name):
        return cls.mappers_by_symbol.get(name, set())

    @classmethod
    def symbols_for(cls, plugin_class):
        return MapperOutput.symbols_by_mapper.get(plugin_class, set())

    @classmethod
    def local_mappers(cls):
        results = []
        for module, c in cls.plugins_by_module.iteritems():
            if len(c) > 1 and cls in c:
                results.extend(c[cls])
        return sorted(results)

    @classmethod
    def add_symbol(cls, file_, filters=[]):
        cls.mappers_by_symbol[file_].add(cls)
        cls.symbols_by_mapper[cls].add(file_)
        cls.filters[file_] |= set(filters)
    
    @classmethod
    def parse_context(cls, context):
        if cls.delegate:
            result = cls.delegate(context)
            return result if isinstance(result, MapperOutput) else cls(result, context.path)
        return cls(cls.process_content(context.content, context.path))
    
    @classmethod
    def process_content(cls, content, path=None):
        pass
    

# alias for mapper plugin registry
Mappers = MapperOutput

# decorator to register a mapper to consume files.
# Wrap a mapper func in a MapperOutput class if necessary.
def mapper(name, filters=[], cluster=False, shared=False):
    def _f(m):
        m = wrap(m, kind=MapperOutput, cluster=cluster, shared=shared)
        m.add_symbol(name, filters)
        return m
    return _f
