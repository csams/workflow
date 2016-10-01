#!/usr/bin/env python

import collections
import logging
import sys


class Registry(type):
    registry = collections.defaultdict(set)
    bases = set()
    plugins_by_module = collections.defaultdict(lambda: collections.defaultdict(set))
    
    @classmethod
    def add_base(cls, name):
        cls.bases.add(name)
        
    @classmethod
    def add_plugin(cls, base, plugin_class):
        cls.registry[base].add(plugin_class)
        cls.plugins_by_module[plugin_class.__module__][base].add(plugin_class)
    
    def __init__(plugin_class, name, bases, attrs):
        if name not in Registry.bases:
            plugin_class.register(Registry)
            plugin_class.serializable_id = '#'.join([plugin_class.__module__, plugin_class.__name__])
            plugin_class.name = '.'.join([plugin_class.__module__, plugin_class.__name__])
            plugin_class.log = logging.getLogger(plugin_class.name)


def split_requirements(requires):
    req_all = []
    req_any = []
    for r in requires:
        if isinstance(r, list):
            req_any.append(r)
        else:
            req_all.append(r)
    return req_all, req_any


def stringify_requirements(requires):
    if isinstance(requires, tuple):
        req_all, req_any = requires
    else:
        req_all, req_any = split_requirements(requires)
    pretty_all = [r.serializable_id for r in req_all]
    pretty_any = [str([r.serializable_id for r in any_list]) for any_list in req_any]
    return "All: %s" % pretty_all + " Any: " + " Any: ".join(pretty_any)


Registry.add_base('Plugin')
class Plugin(object):
    __metaclass__ = Registry
    depends = set()
    shared = False
    cluster = False
    delegate = None
    
    # common registry access methods
    @classmethod
    def all(cls):
        return cls.registry.get(cls)
    
    @classmethod
    def all_shared(cls):
        return set(p for p in cls.registry.get(cls) if p.shared)
    
    @classmethod
    def all_not_shared(cls):
        return set(p for p in cls.registry.get(cls) if not p.shared)
    
    @classmethod
    def all_clustered(cls):
        return set(p for p in cls.registry.get(cls) if p.cluster)
    
    @classmethod
    def all_not_clustered(cls):
        return set(p for p in cls.registry.get(cls) if not p.cluster)

    @classmethod
    def from_module(cls, module):
        return cls.plugins_by_module.get(module, {}).get(cls, set())

    # useful for finding mappers that aren't MapperOutput's yet..
    @classmethod
    def delegators(cls):
        return set(p for p in cls.registry.get(cls) if p.delegate)

    @classmethod
    def local_mappers(cls):
        results = []
        for module, c in cls.plugins_by_module.iteritems():
            if len(c) > 1 and cls in c:
                results.extend(c[cls])
        return sorted(results)

    @classmethod
    def module_dependencies(cls):
        return set()

    def get_missing_requirements(self, d):
        if not self.requires:
            return None
        req_all, req_any = split_requirements(self.requires)
        req_all.extend(self.module_dependencies())
        d = set(d.keys())
        req_all = [r for r in req_all if r not in d]
        req_any = [r for r in req_any if set(r).isdisjoint(d)]
        if not req_all and not req_any:
            return None
        else:
            return req_all, req_any

    def resolve_deps(self, shared):
        for d in self.depends:
            v = shared.get(d)
            self.data[d] = v
            n = d.__name__.lower()
            setattr(self, n, v)

    def convert_context(self, c):
        cp = {}
        for k, v in c.iteritems():
            cp[k.__name__.lower()] = v
        return cp

    def process(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        self.depends |= self.module_dependencies()
        missing_requirements = self.get_missing_requirements(kwargs)
        if not self.requires or not missing_requirements:
            self.resolve_deps(kwargs)
            try:
                if self.delegate:
                    ctx = self.convert_context(kwargs)
                    return self.delegate(*args, **ctx)
                return self.process(*args)
            except Exception as ex:
                self._exception = ex
                raise
        else:
            self.log.debug("Reducer [%s] is missing requirements: %s",
                      self.__module__,
                      stringify_requirements(missing_requirements))


def wrap(plugin, kind=Plugin, depends=set(), cluster=False, shared=False):
    if not (isinstance(plugin, type) and issubclass(plugin, kind)):
        d = plugin
        cls = type(plugin.__name__, (kind,), {'__module__':plugin.__module__})
        mod = sys.modules[plugin.__module__]
        setattr(mod, plugin.__name__, cls)
        plugin = cls
        plugin.delegate = staticmethod(d)
    plugin.depends = depends
    plugin.cluster = cluster
    plugin.shared = shared
    return plugin
