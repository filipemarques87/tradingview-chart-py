
def _full_qualified_name(obj):
    """
    Gets the full qualified name of an object

    Parameters
    ----------
    obj: any
        The object to extract the qualified name
    
    Returns
    -------
    out: str
        The qualified name of the  object
    """
    klass = obj.__class__
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return f'{module}.{klass.__qualname__}'


def _convert_value(value):
    """
    Converts a value to python type.

    Parameters
    ----------
    value: int, float, str
        The parameter to conver
    
    Returns
    -------
    out: int, float or str
        The python value of the variable

    Raises
    ------
    ValueError
        If the value is not supported
    """
    qname = _full_qualified_name(value)
    if qname in ('int', 'float', 'str'):
        return value
    raise ValueError(f'Unknow type f{qname}')


def _convert_from_numpy_ndarray(np_series):
    """
    Convert a numpy array to python list. Only accepts arrays with 1 or 2
    dimensions.

    Parameters
    ----------
    np_series: numpy.ndarray
        The numpy array to be converted

    Returns
    -------
    out: list
        Python list corresponding to the numpay array. 

    Raises
    ------
    ValueError
        If the numpy array has more than 2 dimensions
    """

    # allowed only 1d or 2d array
    if len(np_series.shape) > 2:
        raise ValueError(f'Allowed only 1d or 2d array "\
            "but got {np_series.shape}')

    if len(np_series.shape) == 1:
        return [x.item() for x in np_series]

    converted_array = []
    for row in np_series:
        converted_array.append([_convert_value(x) for x in row])
    return converted_array


def convert_series(series):
    """
    Converts a time series into python builtin type.

    Parameters
    ----------
    series: pd.Series, pd.DataFrame, np.ndarray or list
        The time series to be converted. If it is a python list, not conversion
        is performed.

    Returns
    -------
    out: list
        a python list after conversion

    Raises
    ------
    ValueError
        If the data series type is not supported
    """
    qname = _full_qualified_name(series)
    if qname in ('pandas.core.series.Series', 'pandas.core.frame.DataFrame'):
        return _convert_from_numpy_ndarray(series.values)
    elif qname == 'numpy.ndarray':
        return _convert_from_numpy_ndarray(series)
    elif qname in ('int', 'float', 'list'):
        return series
    raise ValueError(f'Unknow type {qname}')
