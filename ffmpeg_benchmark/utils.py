import statistics


def mean(data):
    if not data:
        return
    if len(data) == 1:
        return data[0]
    return statistics.mean(data)


def stdev(data):
    if not data:
        return
    if len(data) == 1:
        return .0
    return statistics.stdev(data)


def min_(data):
    if not data:
        return
    return min(data)


def max_(data):
    if not data:
        return
    return max(data)


def full_stats(data, prefix=''):
    return {
        f'{prefix}mean': mean(data),
        f'{prefix}stdev': stdev(data),
        f'{prefix}min': min_(data),
        f'{prefix}max': max_(data),
    }
