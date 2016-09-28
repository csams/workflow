#!/usr/bin/env python

import collections
import logging
import sys
from toposort import toposort_flatten
from types import MethodType

log = logging.getLogger(__name__)


class Registry(type):
    registry = collections.defaultdict(set)
    plugin_bases = set()

    @classmethod
    def add_base(cls, base):
        cls.plugin_bases.add(base)

    def __init__(plugin_class, name, bases, attrs):
        if name not in Registry.plugin_bases:
            plugin_class._register(Registry.registry)

            requires = {}
            for k, v in attrs.iteritems():
                d = plugin_class.create_dependency(v)
                if d:
                    d.name = k
                    requires[k] = d

            for policy in plugin_class.__policies__:
                wrapped = set()
                for k, v in policy.deps.iteritems():
                    d = plugin_class.create_dependency(v)
                    if d:
                        d.name = k
                        d.optional = True
                        wrapped.add(d)
                        requires[k] = d
                policy.deps = wrapped
            plugin_class.__requires__ = requires
            super(Registry, plugin_class).__init__(name, bases, attrs)


Registry.add_base('Plugin')
class Plugin(object):
    __metaclass__ = Registry
    __policies__ = []

    enabled = True

    def __init__(self):
        self._deps = {}
        self._exception = None
        cls = self.__class__
        self.log = logging.getLogger('.'.join([cls.__module__, cls.__name__]))

    @classmethod
    def _register(cls, registry):
        registry[Plugin].add(cls)

    def __getitem__(self, k):
        return self._deps[k]

    def get(self, k, default=None):
        try:
            return self.__getitem__(k)
        except:
            return default

    def __contains__(self, k):
        return k in self._deps

    def __call__(self, *args, **kwargs):
        return self.do_process(*args, **kwargs)

    @classmethod
    def create_dependency(cls, dep):
        if isinstance(dep, Dep):
            p = dep.plugin
            if issubclass(p, Plugin):
                return Dependency(p, **dep.kwargs)
            raise Exception('Invalid dependency %s on %s' % (cls, p))

        if type(dep) is Dependency:
            return dep

        try:
            if issubclass(dep, Plugin):
                return Dependency(dep)
        except:
            pass

        return None

    def do_process(self, *args, **kwargs):
        return self.process(*args, **kwargs)

    def process(self, *args, **kwargs):
        pass


Registry.add_base('ClusterPlugin')
class ClusterPlugin(Plugin):
    @classmethod
    def _register(cls, registry):
        registry[ClusterPlugin].add(cls)

    @classmethod
    def create_dependency(cls, dep):
        if isinstance(dep, Dep):
            p = dep.plugin
            if issubclass(p, ClusterPlugin):
                log.info('Creating Dependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
                return Dependency(p, **dep.kwargs)

            if issubclass(p, Plugin):
                log.info('Creating ClusterDependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
                return ClusterDependency(p, **dep.kwargs)

            raise Exception('Invalid Dependency %s on %s' % (cls, p))

        if type(dep) is ClusterDependency:
            log.info('Validating ClusterDependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
            if not issubclass(dep.plugin, Plugin):
                raise Exception('Invalid ClusterDependency %s on %s' % (cls, dep.plugin))
            return dep

        if type(dep) is Dependency:
            log.info(dep)
            log.info('Validating Dependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
            if not issubclass(dep.plugin, ClusterPlugin):
                raise Exception('Invalid Dependency %s on %s' % (cls, dep.plugin))
            return dep

        try:
            if issubclass(dep, ClusterPlugin):
                log.info('Creating default Dependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
                return Dependency(dep)

            if issubclass(dep, Plugin):
                log.info('Creating default Dependency %s(%s) on %s(%s)' % (cls, cls.__bases__, dep.plugin, dep.plugin.__bases__))
                return ClusterDependency(dep)
        except:
            pass


class Policy(object):
    ''' Base classes specify whether any or all of a set of dependencies
        are required.
    '''
    def __init__(self, **kwargs):
        self.deps = kwargs

    def accept(self, deps):
        return True


class Any(Policy):
    def accept(self, resolved_deps):
        return any(d.met(resolved_deps) for d in self.deps)


class All(Policy):
    def accept(self, resolved_deps):
        return all(d.met(resolved_deps) for d in self.deps)


class Dep(object):
    ''' Sugar class for specifying dependencies.

        Used so that Dependency and ClusterDependency never have to be used directly.
    '''
    def __init__(self, plugin, **kwargs):
        self.plugin = plugin
        self.kwargs = kwargs


class Dependency(object):
    ''' Encapsulates a dependency between plugins.

        A dependency may exist Plugin <-> Plugin
        or ClusterPlugin <-> ClusterPlugin but never mixed.
    '''

    def __init__(self, plugin, name=None, optional=False, on_error=False):
        self.plugin = plugin
        self.name = name
        self.optional = optional
        self.on_error = on_error

    def resolve(self, factory, graph):
        plugin_name = '.'.join([self.plugin.__module__, self.plugin.__name__])
        if self.plugin in graph:
            dp = graph[self.plugin]
            if dp._exception and not self.on_error:
                raise Exception('Dependency has exception: %s' % plugin_name)
        else:
            if self.optional:
                dp = None
            else:
                raise Exception('Missing Dependency: %s' % plugin_name)
        return dp

    def met(self, deps):
        d = deps.get(self.name)
        return d is not None

    def __repr__(self):
        plugin = self.plugin
        plugin = '.'.join([plugin.__module__, plugin.__name__])
        dep = '.'.join([self.__class__.__module__, self.__class__.__name__])
        args = (dep, plugin, self.name, self.optional, self.on_error)
        return '%s(%s, name="%s", optional=%s, on_error=%s)' % args


class ClusterDependency(Dependency):
    ''' Encapsulates a dependency between a ClusterPlugin and Plugin
        instances in previous execution graphs.
    '''

    def __init__(self, plugin, role=None, **kwargs):
        self.role = role
        super(ClusterDependency, self).__init__(plugin, **kwargs)

    def resolve(self, factory, graph):
        return None

    def __repr__(self):
        plugin = self.plugin
        plugin = '.'.join([plugin.__module__, plugin.__name__])
        dep = '.'.join([self.__class__.__module__, self.__class__.__name__])
        args = (dep, plugin, self.role, self.name, self.optional, self.on_error)
        return '%s(%s, role="%s", name="%s", optional=%s, on_error=%s)' % args


class PluginFactory(object):
    ''' A subclass of PluginFactory would override create so that
        certain plugins would be created based on file availability
        in an archive.  multi_output files would yield an instance
        of P per relevant file.
    '''

    def __init__(self):
        self.plugins = Registry.registry[Plugin]

    def create_plugin(self, P):
        yield P()

    def run_plugin(self, p):
        return p.do_process(p._deps)

    def verify_deps(self, policies, deps):
        return all(p.accept(deps) for p in policies)

    def resolve_deps(self, requires, graph):
        log.debug('DependsOn: %s', requires)
        log.debug('Graph: %s', graph)
        deps = {}
        for n, d in requires.iteritems():
            deps[n] = d.resolve(self, graph)
        log.debug('ResolvedDeps: %s', deps)
        return deps

    def run_order(self):
        graph = {}
        for p in self.plugins:
            graph[p] = set(r.plugin for r in p.__requires__.values() if type(r) is Dependency)
        return toposort_flatten(graph)

    def _run_plugin(self, P, deps):
        ps = []
        for p in self.create_plugin(P):
            log.debug('Created %s', P.__name__)
            for name, _type in P.__requires__.iteritems():
                dep = deps.get(name)
                p._deps[_type.plugin] = dep
                setattr(p, name, dep)
            try:
                p.output = self.run_plugin(p)
            except Exception as pe:
                p._exception = pe
            ps.append(p)
        return ps

    def run_plugins(self, graph={}):
        for P in self.run_order():
            try:
                if not P.enabled:
                    continue
                log.debug('Resolving %s', P.__name__)
                deps = self.resolve_deps(P.__requires__, graph)
                if not self.verify_deps(P.__policies__, deps):
                    continue
                results = self._run_plugin(P, deps)
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
        self.plugins = Registry.registry[ClusterPlugin]


def plugin(requires=[], optional=[], kind=Plugin, enabled=True, attrs={}):
    '''Syntactic sugar.

       Decorator for creating plugins out of functions.
       Leave kind as Plugin for regular plugins and set
       to ClusterPlugin for plugins that should work on
       cluster archives.
    '''

    def wrapper(func):
        policies = []
        _attrs = attrs if attrs else {}

        # create required dependencies
        for r in requires:
            if isinstance(r, Policy):
                policies.append(r)
            elif isinstance(r, collections.Iterable):
                args = {}
                for a in r:
                    args[a.__name__.lower()] = a
                policies.append(Any(**args))
            else:
                r = kind.create_dependency(r)
                if r:
                    name = r.name if r.name else r.plugin.__name__.lower()
                    r.name = name
                    _attrs[name] = r

        # create optional dependencies
        for r in optional:
            r = kind.create_dependency(r)
            if r:
                r.optional=True
                name = r.name if r.name else r.plugin.__name__.lower()
                r.name = name
                _attrs[name] = r

        _attrs['enabled'] = enabled
        _attrs['__module__'] = func.__module__
        _attrs['__policies__'] = policies
        cls = type(func.__name__, (kind,), _attrs)
        cls.process = MethodType(func, None, cls)
        mod = sys.modules[func.__module__]
        setattr(mod, func.__name__, cls)
        return cls
    return wrapper
