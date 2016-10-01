from collections import defaultdict
from engine.registry import Plugin, Registry, stringify_requirements, wrap
from engine.mapper import Mappers
from engine.util import box, flatten


Registry.add_base('Reducer')
class Reducer(Plugin):

    mappers_by_module = defaultdict(set)

    @classmethod
    def register(cls, registry):
        registry.add_plugin(Reducer, cls)

    @classmethod
    def module_dependencies(cls):
        return Mappers.from_module(cls.__module__)

    # reducer specific registry method.  "rule" is just a 
    # non shared reducer.
    @classmethod
    def all_rules(cls):
        return cls.all_not_shared()
        
    def __init__(self):
        self.data = {}
        self._exception = None

    def __getitem__(self, k):
        return self.data[k]

    def __contains__(self, k):
        return k in self.data

    def get(self, k, default=None):
        try:
            return self.__getitem__(k)
        except:
            return default

    def process(self, local):
        pass

    def __call__(self, local, shared):
        self.depends |= self.module_dependencies()
        missing_requirements = self.get_missing_requirements(shared)
        if not self.requires or not missing_requirements:
            self.resolve_deps(shared)
            try:
                if self.cluster:
                    local = box(local)
                    if self.delegate:
                        return self.delegate(local, self)
                    return self.process(local)
                else:
                    if self.delegate:
                        return self.delegate(local, self)
                    return self.process(local)
            except Exception as ex:
                self._exception = ex
                raise
        else:
            self.log.debug("Reducer [%s] is missing requirements: %s",
                      self.__module__,
                      stringify_requirements(missing_requirements))


#alias for reducer plugin registry
Reducers = Reducer

def reducer(requires=[], optional=[], cluster=False, shared=False):
    def _f(r):
        deps = set(flatten(requires)) | set(optional)
        r = wrap(r, kind=Reducer, depends=deps, cluster=cluster, shared=shared)
        r.requires = requires
        r.optional = optional
        return r
    return _f    
