from collections import defaultdict


def map_reduce(data, emitfunc=lambda rec: [(rec,)], reducefunc=lambda v, k: v):
    """perform a "map-reduce" on the data

    emitfunc(datum): return an iterable of key-value pairings as (key, value). alternatively, may
        simply emit (key,) (useful for reducefunc=len)
    reducefunc(values): applied to each list of values with the same key; defaults to just
        returning the list
    data: iterable of data to operate on
    """
    mapped = defaultdict(list)
    for rec in data:
        for emission in emitfunc(rec):
            try:
                k, v = emission
            except ValueError:
                k, v = emission[0], None
            mapped[k].append(v)

    def _reduce(k, v):
        try:
            return reducefunc(v, k)
        except TypeError:
            return reducefunc(v)

    return dict((k, _reduce(k, v)) for k, v in mapped.iteritems())
