#!/usr/bin/env python
import logging
from types import MethodType
import sys

log = logging.getLogger(__name__)


class Registry(type):
    registry = set()
    cluster_registry = set()

    def __init__(plugin_class, name, bases, attrs):
        if name not in ('Plugin', 'ClusterPlugin'):
            plugin_class._register(Registry)
            requires = {}
            for k, v in attrs.iteritems():
                d = plugin_class.create_dependency(v)
                if d:
                    requires[k] = d
            plugin_class.__requires__ = requires
            super(Registry, plugin_class).__init__(name, bases, attrs)


class Plugin(object):
    __metaclass__ = Registry

    def __init__(self):
        self._data = {}
        self._exception = None
        cls = self.__class__
        self.log = logging.getLogger('.'.join([cls.__module__, cls.__name__]))

    @classmethod
    def _register(cls, registry):
        registry.registry.add(cls)

    def __getitem__(self, k):
        return self._data[k]

    def get(self, k, default=None):
        try:
            return self.__getitem__(k)
        except:
            return default

    def __contains__(self, k):
        return k in self._data

    def __call__(self):
        return self.process()

    @staticmethod
    def create_dependency(dep):
        if isinstance(dep, Dep):
            p = dep.plugin
            if issubclass(p, Plugin):
                return Dependency(p, **dep.kwargs)

            raise Exception('Invalid Dependency: %s' % dep.plugin)
        if type(dep) is Dependency:
            return dep

        try:
            if issubclass(dep, Plugin):
                return Dependency(dep)
        except:
            pass

        return None

    def process(self, *args):
        return None


class ClusterPlugin(Plugin):
    @classmethod
    def _register(cls, registry):
        registry.cluster_registry.add(cls)

    @staticmethod
    def create_dependency(dep):
        if isinstance(dep, Dep):
            p = dep.plugin
            if issubclass(p, ClusterPlugin):
                return Dependency(p, **dep.kwargs)

            if issubclass(p, Plugin):
                return ClusterDependency(p, **dep.kwargs)

            raise Exception('Invalid Dependency: %s' % dep.plugin)

        if type(dep) is Dependency:
            if not issubclass(dep.plugin, ClusterPlugin):
                raise Exception('Invalid Dependency: %s' % dep.plugin)
            return dep

        try:
            if issubclass(dep, ClusterPlugin):
                return Dependency(dep)

            if issubclass(dep, Plugin):
                return ClusterDependency(dep)
        except:
            pass

        return None


class Dep(object):
    '''Helper class for specifying dependencies so that Dependency
       and ClusterDependency never have to be used directly.'''
    def __init__(self, plugin, **kwargs):
        self.plugin = plugin
        self.kwargs = kwargs


class Dependency(object):
    '''Encapsulates a dependency between plugins.

       A dependency may exist between Plugin <-> Plugin
       or ClusterPlugin <-> ClusterPlugin but never mixed.'''

    def __init__(self, plugin, name=None, optional=False, on_error=False):
        self.plugin = plugin
        self.name = name
        self.optional = optional
        self.on_error = on_error


class ClusterDependency(Dependency):
    '''Encapsulates a dependency between a ClusterPlugin and previous execution graphs.'''

    def __init__(self, plugin, role=None, **kwargs):
        self.role = role
        super(ClusterDependency, self, **kwargs)


class PluginFactory(object):
    ''' Subclass of PluginFactory would override create so that
        certain plugins would be created based on file
        availability in an archive.  multi_output files would yield
        an instance of P per relevant file.
    '''

    def create(self, P):
        yield P()

    @property
    def plugins(self):
        return Registry.registry

    def resolve_dep(self, name, dep, graph):
        if dep.plugin not in graph:
            if dep.optional:
                dp = None
            else:
                raise Exception('Missing Dependency: %s' % name)
        else:
            dp = graph[dep.plugin]
            if dp._exception and not dep.on_error:
                raise Exception('Dependency has exception: %s' % name)
        return dp

    def resolve_deps(self, P, graph):
        log.debug('Resolving %s', P.__name__)
        log.debug('DependsOn: %s', P.__requires__)
        log.debug('Graph: %s', graph)
        deps = {}
        for n, d in P.__requires__.iteritems():
            deps[n] = self.resolve_dep(n, d, graph)
        log.debug('ResolvedDeps: %s', deps)
        return deps

    @staticmethod
    def run_order(plugins):
        stack = []
        seen = set()
        while plugins or stack:
            cur = stack.pop() if stack else plugins.pop()
            if cur in seen:
                continue
            deps = set([r.plugin for r in cur.__requires__.values() if type(r) is Dependency]) - seen
            if not deps:
                seen.add(cur)
                yield cur
            else:
                if cur in stack:
                    raise Exception('Dependency Cycle: %s already in %s' % (cur, stack))
                stack.append(cur)
                stack.extend(deps)

    def run_plugin(self, P, deps):
        ps = []
        for p in self.create(P):
            log.debug('Created %s', P.__name__)
            for name, _type in P.__requires__.iteritems():
                dep = deps.get(name)
                p._data[_type.plugin] = dep
                setattr(p, name, dep)
            try:
                p.process()
            except Exception as pe:
                log.exception(pe)
                p._exception = pe
            ps.append(p)
        return ps

    def run_plugins(self):
        graph = {}
        for P in self.run_order(self.plugins):
            try:
                deps = self.resolve_deps(P, graph)
                results = self.run_plugin(P, deps)
                if results:
                    graph[P] = results if len(results) > 1 else results[0]
            except Exception as e:
                log.exception(e)
        return graph


class ClusterPluginFactory(PluginFactory):
    '''ClusterPluginFactory should be initialized with a set of graphs
       that are the result of PluginFactory.run_plugins calls for each
       archive in a cluster archive.  This would then be used to satisfy
       the ClusterDependency requirements of ClusterPlugins.
    '''

    def __init__(self, graphs):
        self.graphs = graphs

    @property
    def plugins(self):
        return Registry.cluster_registry

    def resolve_deps(self, P, graph):
        log.debug('Resolving %s', P.__name__)
        log.debug('DependsOn: %s', P.__requires__)
        log.debug('Role Graph: %s', self.graphs)
        log.debug('Graph: %s', graph)
        deps = {}
        for n, d in P.__requires__.iteritems():
            if isinstance(d, ClusterDependency):
                # dig things out of self.graphs for the deps
                pass
            else:
                deps[n] = self.resolve_dep(n, d, graph)
        log.debug('ResolvedDeps: %s', deps)
        return deps

def reducer(requires=[], kind=Plugin):
    '''Syntactic sugar.
       Decorator for creating plugins out of functions.
       Leave kind as Plugin for regular plugins and set
       to ClusterPlugin for plugins that should work on
       cluster archives.
    '''

    def wrapper(func):
        attrs = {}
        for r in requires:
            r = kind.create_dependency(r)
            if r:
                name = r.name if r.name else r.plugin.__name__.lower()
                attrs[name] = r
        attrs['__module__'] = func.__module__
        cls = type(func.__name__, (kind,), attrs)
        cls.process = MethodType(func, None, cls)
        mod = sys.modules[func.__module__]
        setattr(mod, func.__name__, cls)
        return cls
    return wrapper
