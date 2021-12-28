
def _full_qualified_name(o):
    klass = o.__class__
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return f'{module}.{klass.__qualname__}'


def _convert_value(value):
    qname = _full_qualified_name(value)
    if qname in ('int', 'float', 'str'):
        return value
    raise ValueError(f'Unknow type f{qname}')


def _convert_from_numpy_ndarray(np_series):
    # allowed only 1d or 2d array
    if len(np_series.shape) > 2:
        raise ValueError(
            f'Allowed only 1d or 2d array but got {np_series.shape}')

    if len(np_series.shape) == 1:
        return [x.item() for x in np_series]

    converted_array = []
    for row in np_series:
        converted_array.append([_convert_value(x) for x in row])
    return converted_array


def convert_series(series):
    qname = _full_qualified_name(series)
    if qname in ('pandas.core.series.Series', 'pandas.core.frame.DataFrame'):
        return _convert_from_numpy_ndarray(series.values)
    elif qname == 'numpy.ndarray':
        return _convert_from_numpy_ndarray(series)
    elif qname in ('int', 'float', 'list'):
        return series
    raise ValueError(f'Unknow type {qname}')
