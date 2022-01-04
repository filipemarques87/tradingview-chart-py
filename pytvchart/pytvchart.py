import datetime
import json
import numpy as np
import uuid
import webview

import pytvchart.util as util
from pytvchart.theme import TVCHART_THEME


# colour available to switch between chart lines
# COLOR_PALLET = ['rgba(69,114,167,255)',
#                 'rgba(170,70,67,255)',
#                 'rgba(137,165,78,255)',
#                 'rgba(113,88,143,255)',
#                 'rgba(65,152,175,255)',
#                 'rgba(219,132,61,255)',
#                 'rgba(147,169,207,255)']


class TradingViewEvent:
    '''
    This class holds informations for a single series to be shown in the figure.
    I can be a candle stick series, a line series, volume series, ...
    '''

    def __init__(self, time, text, position, shape, color):
        self.time = time
        self.text = text
        self.position = position
        self.shape = shape
        self.color = color

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class TradingViewSeries:
    '''
    This class holds informations for a single series to be shown in the figure.
    I can be a candle stick series, a line series, volume series, ...
    '''

    def __init__(self, series, type, **kwargs):
        self.series = series
        self.type = type
        self.config = kwargs

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class TradingViewFigure:
    '''
    This class holds the information related with on figure.
    A figure is composed by a candlestick series extra series like volume,
    single line, ....
    Also holds the configuration for those series.

    First serie correspond always to a candle stick series
    '''

    def __init__(self, title='', theme='light'):
        self.series = []
        self.events = []
        self.title = title
        self.theme = theme
        self.config = {
            'backgroundColor': TVCHART_THEME[theme]['backgroundColor'],
            'textColor': TVCHART_THEME[theme]['textColor'],
            'borderColor': TVCHART_THEME[theme]['borderColor'],
            'gridColor': TVCHART_THEME[theme]['gridColor']
        }

    def add_series(self, series):
        ''' Adds a new series to this figure '''
        if series.type == 'ohlc':
            # only 1 candlestick chart is allowed per figure
            result = list(filter(lambda x: x.type == 'ohlc', self.series))
            if len(result) > 0:
                raise ValueError()

            self.series = [series] + self.series
        else:
            self.series.append(series)

    def add_event(self, event):
        self.events = sorted(
            self.events + [event], key=lambda row: row.time)

    def serialize(self):
        return {
            'config': json.dumps(self.config),
            'series': [s.serialize() for s in self.series],
            'events': [s.serialize() for s in self.events]
        }


class WebviewApi:
    """
    Class used to comunicate between python and webview. Every figure will have
    an intance of this class
    """

    def __init__(self, figure):
        """
        Creates a new WebviewApi instance

        Parameters
        ----------
        figure: TradingViewFigure
            The figure which is associated with this instance
        """
        self.figure = figure

    def request_data(self):
        """
        This method is called from JS code and will request all data to be
        shown on the figure.

        Returns
        -------
        out: list
            Returns a list containing all series of the figure. Every series
            is a JSON object serialized into a string, so to be used, this
            string must be parsed into JSON before in the JS side
        """
        return self.figure.serialize()


def _create_new_figure(id=None, title=''):
    """
    Creates a new figure.

    Parameters
    ----------
    id: str, optional
        Id of the figure. If it is not provided it will be generated one
    title: str
        Title of the figure to be created
    """
    global tvchart_figures
    global current_tvchart_figure

    id = id or str(uuid.uuid4())
    current_tvchart_figure = TradingViewFigure(title=title)
    tvchart_figures[id] = current_tvchart_figure


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
    up_colour: str
        Colour of the candle when the close price is greater than the open
        price.
    down_colour: str
        Colour of the candle when the open price is greater than the close
        price.
    wick_up_colour: str
        Colour of the candle wick when the close price is greater than the open
        price.
    wick_down_colour: str
        Colour of the candle wick when the open price is greater than the close
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
    #if current_tvchart_figure is None:
    #    raise ValueError(f'Cannot add a candle stick serie. "\
    #            "Figure {current_tvchart_figure} already exists')

    ohlc_series = util.convert_series(np_ohlc_series)
    ignore, ncolumns = np.shape(ohlc_series)
    if ncolumns < 5:
        raise ValueError(f'Expect 5 columns: time, open, high, low, close "\
            "but got {ncolumns}')

    # converts the column date to timestamp
    if date_format is not None:
        for row in ohlc_series:
            row[0] = int(datetime.datetime.strptime(
                row[0], date_format).timestamp())

    # prepare the data to be used in TradingView library
    ohlc_series = [{
        'time': row[0],
        'open': row[1],
        'high': row[2],
        'low': row[3],
        'close': row[4]}
        for row in ohlc_series]

    cs_theme = TVCHART_THEME[current_tvchart_figure.theme]['candlestickChart']

    tv_series = TradingViewSeries(
        ohlc_series, 'ohlc', name=name,
        show_legend=show_legend, legend_index=0, date_format=date_format,
        up_colour=cs_theme['up_colour'],
        down_colour=cs_theme['down_colour'],
        wick_up_colour=cs_theme['wick_up_colour'],
        wick_down_colour=cs_theme['wick_down_colour'])

    current_tvchart_figure.add_series(tv_series)


def plot_line(
    np_line_series, name=None, colour=None, show_legend=True
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
    colour: str
        Colour of the line. If it is not goven then uses the colour from the
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
        #raise ValueError(f'Figure {current_tvchart_figure} does not exists')
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
    cs_theme = TVCHART_THEME[current_tvchart_figure.theme]['line_chart']
    colour_pallet = cs_theme['colour_pallet']
    if colour is None:
        index = len(
            [s for s in current_tvchart_figure.series if s.type == 'line'])
        colour = colour_pallet[index % len(colour_pallet)]

    legend_index = len(
        [s for s in current_tvchart_figure.series if s.config['show_legend']])

    if name is None:
        name = f'Line {index + 1}'

    tv_series = TradingViewSeries(
        line_series, 'line', name=name, colour=colour, show_legend=show_legend,
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
    colour_up: str
        Colour of the bar when the close price is greater than the open price.
    colour_down: str
        Colour of the bar when the open price is greater than the close price.
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
        #raise ValueError(f'Figure {current_tvchart_figure} does not exists')
        _create_new_figure()

    volume_series = util.convert_series(np_volume_series)
    if len(np.shape(volume_series)) != 1:
        raise ValueError(f'Expect 1 column but got "\
            "{len(np.shape(volume_series))}')

    ohlc_series = current_tvchart_figure.series[0].series
    if len(volume_series) != len(ohlc_series):
        raise ValueError(f'Line lenght and candle stick length are different:"\
            "{len(volume_series)} != {len(ohlc_series)}')

    cs_theme = TVCHART_THEME[current_tvchart_figure.theme]['volume_chart']
    colour_up = cs_theme['colour_up']
    colour_down = cs_theme['colour_down']

    volume_series = [{
        'time': row[0]['time'],
        'value': row[1],
        'color': colour_up if row[0]['open'] < row[0]['close'] else colour_down}
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
        Date format to parse the time parameter. If it is not provided the time
        must be a unix timestamp
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
        shape=arrowUp, colour=#e91e63 and text start with 'Sell @'. If it
        value is but then the following configuration is used:
        position=aboveBar, shape=arrowUp, colour=#2196F3 and text start with
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

    #current_figure = tvchart_figures[current_tvchart_figure]
    #date_format = current_figure.series[0].config['date_format']

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
    webview.start(debug=True)


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
        _create_new_figure(id=id, title=title, theme=theme)
    else:
        current_tvchart_figure = tvchart_figures[id]

    return id


current_tvchart_figure = None
tvchart_figures = {}
