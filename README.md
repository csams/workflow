# Workflow Engine

## Installation
* virtualenv .
* source bin/activate
* pip install --upgrade pip
* pip install -r requirements.txt

## Plugins 
Plugins are `Plugin` subclasses with a `process` method and zero or more dependencies on
other `Plugin` subclasses.  Dependencies are defined as class level attributes and are
accessed as instance variables when process is called.

Dependencies can be specified by direct reference to another Plugin subclass:

```python

class A(Plugin):
    pass

class B(Plugin):
    a = A
    def process(self):
        self.log.info(self.a)
```

If a dependency is optional, use the `Dep` helper class with the `optional` keyword:

```python

class A(Plugin):
    pass

class B(Plugin):
    a = Dep(A, optional=True)
    def process(self):
        self.log.info(self.a)
```

If a dependency should be provided even if it threw an exception during processing,
use the `Dep` helper class with the `on_error` keyword.  If the dependency throws
an exception, it will be accessible through the `_exception` attribute.

```python
class A(Plugin):
    def process(self):
        raise Exception("Boom!")

class B(Plugin):
    a = Dep(A, on_error=True)
    def process(self):
        self.log.info(self.a._exception)
```

Combine `optional` and `on_error` if the plugin should always execute regardless of a dependency's
state.

```python
class A(Plugin):
    def process(self):
        raise Exception("Boom!")

class B(Plugin):
    a = Dep(A, optional=True, on_error=True)
    def process(self):
        self.log.info(self.a._exception)
```

If any one of a set of dependencies should be met, use the `Any` helper,
and define it in a `__policies__` class attribute.

```python
class A(Plugin):
    pass

class B(Plugin):
    a = Dep(A, optional=True, on_error=True)
    def process(self):
        self.log.info(self.a)

class C(Plugin):
    __policies__ = [Any(a=A, b=B)]
    def process(self):
        self.log.info('One of self.a and self.b should not be None.')
        self.log.info(self.a)
        self.log.info(self.b)
```

A `Plugin` can be disabled by setting `enabled` to false

```python
class A(Plugin):
    enabled = False
```


The `@reducer` decorator is provided to help with definitions and
to implement an existing API.  An @reducer function is converted
to a class of the same name as the function behind the scenes, and
the function itself is used as the process method for the class.

```python
@reducer
def A(shared):
    pass

@reducer(optional=[A])
def B(shared):
    shared.log.info(shared.a)

@reducer(required=[[A, B]])
def C(shared):
    shared.log.info(shared.a)
    shared.log.info(shared.b)

@reducer(required=[[A, B]], enabled=False)
def D(shared):
    shared.log.info(shared.a)
    shared.log.info(shared.b)
```

Plugins are executed by instantiating a PluginFactory and calling `run_plugins`.
The return value is a dictionary of all Plugin instances that ran.

```python
graph = PluginFactory().run_plugins()
```

## Cluster Plugins
