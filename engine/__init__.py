from toposort import toposort_flatten


def run_order(plugins):
    graph = {}
    for p in plugins:
        graph[p] = p.depends
    return toposort_flatten(graph)


def run_mappers(plugins):
    pass


def run_reducers(plugins, ctx):
    pass
