import datetime
import json
import numpy as np
import pytz
import uuid
import webview

import pytvchart.util as util
from pytvchart.theme import THEMES


class TradingViewEvent:
    """ Holds a single event to be shown on the figure """

    def __init__(self, time, text, position, shape, color):
        self.time = time
        self.text = text
        self.position = position
        self.shape = shape
        self.color = color

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class TradingViewSeries:
    """ Holds a single series to be shown on the figure """

    def __init__(self, series, type, **kwargs):
        self.series = series
        self.type = type
        self.config = kwargs

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class TradingViewFigure:
    """ This class holds the information related with on figure """

    def __init__(self, title='', theme='light'):
        self.series = []
        self.events = []
        self.title = title
        self.theme = theme
        self.config = {
            'backgroundColor': THEMES[theme]['backgroundColor'],
            'textColor': THEMES[theme]['textColor'],
            'borderColor': THEMES[theme]['borderColor'],
            'gridColor': THEMES[theme]['gridColor']
        }

    def add_series(self, series):
        """ Adds a new series to this figure """
        if series.type == 'ohlc':
            # only 1 candlestick chart is allowed per figure
            result = list(filter(lambda x: x.type == 'ohlc', self.series))
            if len(result) > 0:
                raise ValueError()

            self.series = [series] + self.series
        else:
            self.series.append(series)

    def add_event(self, event):
        """ Adds a single event to this figure """
        self.events = sorted(
            self.events + [event], key=lambda row: row.time)

    def serialize(self):
        """ Serializes the this figure to be sent to tradingview library"""
        return {
            'config': json.dumps(self.config),
            'series': [s.serialize() for s in self.series],
            'events': [s.serialize() for s in self.events]
        }


class WebviewApi:
    """ Serves as a bridge between python code and tradingview library """

    def __init__(self, figure):
        self.figure = figure

    def request_data(self):
        """ Returns serialized data to tradingview library """
        return self.figure.serialize()


def _create_new_figure(id=None, title='', theme='light'):
    """ Creates a new figure. """
    global tvchart_figures
    global current_tvchart_figure

    id = id or str(uuid.uuid4())

    current_tvchart_figure = TradingViewFigure(title=title, theme=theme)
    tvchart_figures[id] = current_tvchart_figure
    return id


def plot_candlestick(
    np_ohlc_series, name='', date_format=None, show_legend=True
):
    """
    Plots a candlestick data series.

    Parameters
    ----------
    np_ohlc_series: list
        The array that holds the ohlc data. It can be a pandas dataframe, 
        a numpy array or a python list. It is expected to have at least 5
        columns where the 5 firsts are: time, open, high, low close
    name: str, optional
        Name of the time ohlc time series
    date_format: str, optional
        Date format of the time in the ohlc data. If null, not conversion is
        done but this implies that the time is a unix timestamp
    show_legend: bool, default: True
        True to show the legend of this timeseries, false otherwise.
    up_color: str
        color of the candle when the close price is greater than the open
        price.
    down_color: str
        color of the candle when the open price is greater than the close
        price.
    wick_up_color: str
        color of the candle wick when the close price is greater than the open
        price.
    wick_down_color: str
        color of the candle wick when the open price is greater than the close
        price.

    Raises
    ------
    ValueError
        If the some input is invalid
    
    """
    global tvchart_figures
    global current_tvchart_figure

    if current_tvchart_figure is None:
        _create_new_figure()

    ohlc_series = util.convert_series(np_ohlc_series)
    ignore, ncolumns = np.shape(ohlc_series)
    if ncolumns < 5:
        raise ValueError(f'Expect 5 columns: time, open, high, low, close "\
            "but got {ncolumns}')

    # converts the column date to timestamp
    if date_format is not None:
        for row in ohlc_series:
            row[0] = int(datetime.datetime.strptime(
                row[0], date_format).replace(tzinfo=pytz.utc).timestamp())

    # prepare the data to be used in TradingView library
    ohlc_series = [{
        'time': row[0],
        'open': row[1],
        'high': row[2],
        'low': row[3],
        'close': row[4]}
        for row in ohlc_series]

    cs_theme = THEMES[current_tvchart_figure.theme]['candlestickChart']

    tv_series = TradingViewSeries(
        ohlc_series, 'ohlc', name=name,
        show_legend=show_legend, legend_index=0, date_format=date_format,
        up_color=cs_theme['up_color'],
        down_color=cs_theme['down_color'],
        wick_up_color=cs_theme['wick_up_color'],
        wick_down_color=cs_theme['wick_down_color'])

    current_tvchart_figure.add_series(tv_series)


def plot_line(
    np_line_series, name=None, color=None, show_legend=True
):
    """
    Plots a single line.

    Parameters
    ----------
    np_line_series: list
        The array that holds the line data. It can be a pandas dataframe, 
        pandas series, numpy array or a python list. It is expected to have
        only 1 column
    name: str, optional
        Name of the time line series. The default value is 'Line {index}'
    color: str
        color of the line. If it is not goven then uses the color from the
        theme COLOR_PALLET
    show_legend: bool
        True to show the legend of this timeseries, false otherwise. Default
        value is True
    
    Raises
    ------
    ValueError
        If a candlestick data was not previously ploted or if the some input
        is invalid
    
    """
    global tvchart_figures
    global current_tvchart_figure

    if current_tvchart_figure is None:
        _create_new_figure()

    line_series = util.convert_series(np_line_series)
    if len(np.shape(line_series)) != 1:
        raise ValueError(f'Expect 1 column but got {len(line_series.shape)}')

    ohlc_series = current_tvchart_figure.series[0].series
    if len(line_series) != len(ohlc_series):
        raise ValueError(f'Line lenght and candle stick length are different:"\
            "{len(line_series)} != {len(ohlc_series)}')

    # prepare the data to be used in TradingView library
    line_series = [{
        'time': row[0]['time'],
        'value': row[1]}
        for row in zip(ohlc_series, line_series) if not np.isnan(row[1])]

    # get correct line color if not set
    cs_theme = THEMES[current_tvchart_figure.theme]['line_chart']
    color_pallet = cs_theme['color_pallet']
    if color is None:
        index = len(
            [s for s in current_tvchart_figure.series if s.type == 'line'])
        color = color_pallet[index % len(color_pallet)]

    legend_index = len(
        [s for s in current_tvchart_figure.series if s.config['show_legend']])

    if name is None:
        name = f'Line {index + 1}'

    tv_series = TradingViewSeries(
        line_series, 'line', name=name, color=color, show_legend=show_legend,
        legend_index=legend_index)

    current_tvchart_figure.add_series(tv_series)


def plot_volume(np_volume_series, name='Vol', show_legend=True):
    """
    Plots a volume.

    Parameters
    ----------
    np_volume_series: list
        The array that holds the volume data. It can be a pandas dataframe, 
        pandas series, numpy array or a python list. It is expected to have
        only 1 column
    name: str
        Name of the time line series. The default value is Vol
    color_up: str
        color of the bar when the close price is greater than the open price.
    color_down: str
        color of the bar when the open price is greater than the close price.
    show_legend: bool
        True to show the legend of this timeseries, false otherwise. Default
        value is True
    
    Raises
    ------
    ValueError
        If a candlestick data was not previously ploted or if the some input
        is invalid
    
    """
    ''' Adds volume into candlestick chart '''
    global tvchart_figures
    global current_tvchart_figure

    if current_tvchart_figure is None:
        _create_new_figure()

    volume_series = util.convert_series(np_volume_series)
    if len(np.shape(volume_series)) != 1:
        raise ValueError(f'Expect 1 column but got "\
            "{len(np.shape(volume_series))}')

    ohlc_series = current_tvchart_figure.series[0].series
    if len(volume_series) != len(ohlc_series):
        raise ValueError(f'Line lenght and candle stick length are different:"\
            "{len(volume_series)} != {len(ohlc_series)}')

    cs_theme = THEMES[current_tvchart_figure.theme]['volume_chart']
    color_up = cs_theme['color_up']
    color_down = cs_theme['color_down']

    volume_series = [{
        'time': row[0]['time'],
        'value': row[1],
        'color': color_up if row[0]['open'] < row[0]['close'] else color_down}
        for row in zip(ohlc_series, volume_series) if not np.isnan(row[1])]

    legend_index = len(
        [s for s in current_tvchart_figure.series if s.config['show_legend']])

    tv_volume = TradingViewSeries(
        volume_series, 'volume', name=name, show_legend=show_legend,
        legend_index=legend_index)

    current_tvchart_figure.add_series(tv_volume)


def plot_event(
    time, text, date_format=None, type=None, position='aboveBar',
    shape='arrowDown', color='#000'
):
    """
    Plots an event. An event is a marker in the chart with some description.
    Could indicate a buy signal, a sell signal or other event.

    Parameters
    ----------
    time: str, int
        Time when the event occured. Can be a unix timestamp or could a date
        string. If it is a date string, a date format must be provided
    date_format: str, optional
        Date format to parse the time parameter. If it is not provided the
        date format from candlestick chart is used
    position: str
        Position of the text in the chart. The possible values are: aboveBar,
        belowBar or inBar
    shape: str, optional
        Shape of the marker. The possible values are: circle, square, arrowUp
        or arrowDown
    color: str, default: #000
        Color of the marker and text
    type: str, optional
        Type of the event. The possible values are: buy or sell. If its value
        is buy the follow configuration is used: position=belowBar,
        shape=arrowUp, color=#e91e63 and text start with 'Sell @'. If it
        value is but then the following configuration is used:
        position=aboveBar, shape=arrowUp, color=#2196F3 and text start with
        'Buy @'

    Raises
    ------
    ValueError
        If either the position, shape or type are invalid
    """
    if position not in (None, '', 'aboveBar', 'belowBar', 'inBar'):
        raise ValueError(f'Invalid position {position}')

    if shape not in (None, '', 'circle', 'square', 'arrowUp', 'arrowDown'):
        raise ValueError(f'Invalid shape {shape}')

    if type not in (None, '', 'sell', 'buy'):
        raise ValueError(f'Invalid type {type}')

    if type == 'sell':
        position, color, shape, text = \
            'aboveBar',  '#e91e63', 'arrowDown', f'Sell @ {text}'
    elif type == 'buy':
        position, color, shape, text = \
            'belowBar',  '#2196F3', 'arrowUp', f'Buy @ {text}'

    ohcl_series = [series for series in current_tvchart_figure.series
                   if series.type == 'ohlc'][0]
    date_format = date_format or ohcl_series.config['date_format']
    if date_format is not None:
        time = int(datetime.datetime.strptime(time, date_format).timestamp())

    tv_event = TradingViewEvent(time, text, position, shape, color)
    current_tvchart_figure.add_event(tv_event)


def show():
    """
    Shows the figure(s).
    """
    global tvchart_figures

    for idx, id in enumerate(tvchart_figures):
        figure = tvchart_figures[id]
        title = figure.title or f'Figure {idx + 1}'
        webview_api = WebviewApi(figure)
        window = webview.create_window(title, 'pytvchart/web/index.html',
                                       js_api=webview_api)
    webview.start(debug=False)


def figure(id=None, title='', theme='light'):
    """
    Creates a new figure. A figure is a window where the charts will
    be rendered.

    Parameters
    ----------
    id: str, optional
        Id of the figure to create. If it is not provided, it will be
        generated. The id could be used to add charts to figures in an
        alternate way.
    title: str, default: <empty>
        Title of the figure

    Returns
    -------
    out: str
        The id of the created figure
    """
    global tvchart_figures
    global current_tvchart_figure

    if id is None or id not in tvchart_figures:
        # the new figure is added inside of the function
        id = _create_new_figure(id=id, title=title, theme=theme)
    else:
        current_tvchart_figure = tvchart_figures[id]

    return id


current_tvchart_figure = None
tvchart_figures = {}
