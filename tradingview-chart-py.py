import webview
import json
from dataclasses import dataclass, fields
import datetime
import pandas as pd
import numpy as np

import util


COLOR_PALLET = ['rgba(69,114,167,255)',
                'rgba(170,70,67,255)',
                'rgba(137,165,78,255)',
                'rgba(113,88,143,255)',
                'rgba(65,152,175,255)',
                'rgba(219,132,61,255)',
                'rgba(147,169,207,255)']


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

    def __init__(self, ohlc_series, title=''):
        self.series = [ohlc_series]
        self.title = title

    def add_series(self, series):
        ''' Adds a new series to this figure '''
        self.series.append(series)

    def serialize(self):
        return [s.serialize() for s in self.series]


class WebviewApi:
    def __init__(self, figure):
        ''' Class used to communiate between python code and tradingview char library '''
        self.figure = figure

    def _parse_user_config(self, **kwargs):
        ''' Parses the user configurations and save those options in ChartConfig object '''
        chart_config = ChartConfig()
        for field in fields(ChartConfig):
            if field.name in kwargs:
                setattr(chart_config, field.name, kwargs[field.name])

        return chart_config

    def request_data(self):
        response = {
            'series': self.figure.serialize()
            #'config': json.dumps(dataclasses.asdict(self.chart_cofig))
        }
        return response


def plot_candlestick(np_ohlc_series, **kwargs):
    ''' Plots candlestick data '''
    global current_figure_index
    global trading_view_figures

    ohlc_series = util.convert_series(np_ohlc_series)

    if current_figure_index < len(trading_view_figures):
        raise ValueError(
            f'Cannot add a candle stick serie. Figure {current_figure_index} already exists')

    # if not isinstance(ohlc_series, np.ndarray):
    #     raise ValueError('Candle stick data must be a numpy ndarray')

    ignore, ncolumns = np.shape(ohlc_series)
    if ncolumns < 5:
        raise ValueError(
            f'Expect 5 columns: time, open, high, low, close but got {ncolumns}')

    # converts the column date to timestamp
    date_format = kwargs['date_format']
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

    trading_view_figures.append(TradingViewFigure(
        TradingViewSeries(ohlc_series, 'ohlc')))


def plot_line(np_line_series, **kwargs):
    ''' Adds a plot into candlestick chart '''
    global current_figure_index
    global trading_view_figures

    if current_figure_index >= len(trading_view_figures):
        raise ValueError(f'Figure {current_figure_index} does not exists')

    current_figure = trading_view_figures[current_figure_index]
    line_series = util.convert_series(np_line_series)
    ohlc_series = current_figure.series[0].series

    # if not isinstance(line_series, np.ndarray):
    #     raise ValueError('Candle stick data must be a numpy ndarray')

    if len(np.shape(line_series)) != 1:
        raise ValueError(
            f'Expect 1 column but got {len(line_series.shape)}')

    if len(line_series) != len(ohlc_series):
        raise ValueError(
            f'Line lenght and candle stick length are different: {len(line_series)} != {len(ohlc_series)}')

    line_series = [{'time': row[0]['time'], 'value': row[1]}
                   for row in zip(ohlc_series, line_series) if not np.isnan(row[1])]

    # get correct line color if not set
    if 'color' not in kwargs:
        total_lines = len(
            [s for s in current_figure.series if s.type == 'line'])
        kwargs['color'] = COLOR_PALLET[total_lines % len(COLOR_PALLET)]

    kwargs['index'] = total_lines
    current_figure.add_series(TradingViewSeries(line_series, 'line', **kwargs))


def plot_volume(np_volume_series, **kwargs):
    ''' Adds volume into candlestick chart '''
    global current_figure_index
    global trading_view_figures

    if current_figure_index >= len(trading_view_figures):
        raise ValueError(f'Figure {current_figure_index} does not exists')

    current_figure = trading_view_figures[current_figure_index]
    volume_series = util.convert_series(np_volume_series)
    ohlc_series = current_figure.series[0].series

    # if not isinstance(volume_series, np.ndarray):
    #     raise ValueError('Candle stick data must be a numpy ndarray')

    if len(np.shape(volume_series)) != 1:
        raise ValueError(
            f'Expect 1 column but got {len(np.shape(volume_series))}')

    if len(volume_series) != len(ohlc_series):
        raise ValueError(
            f'Line lenght and candle stick length are different: {len(volume_series)} != {len(ohlc_series)}')

    up_color = 'rgba(0, 150, 136, 0.8)' if 'color_up' not in kwargs else kwargs[
        'color_up']
    down_color = 'rgba(255,82,82, 0.8)' if 'color_down' not in kwargs else kwargs[
        'color_down']
    volume_series = [{'time': row[0]['time'], 'value': row[1], 'color': up_color if row[0]['open'] < row[0]['close'] else down_color}
                     for row in zip(ohlc_series, volume_series) if not np.isnan(row[1])]

    current_figure.add_series(TradingViewSeries(
        volume_series, 'volume', **kwargs))


def show():
    ''' Shows the chart '''
    global trading_view_figures

    for figure in trading_view_figures:
        webview_api = WebviewApi(figure)
        window = webview.create_window(
            figure.title, 'index.html', js_api=webview_api)
    # print(window)
    webview.start(debug=True)


def figure():
    global current_figure_index

    current_figure_index += 1


current_figure_index = 0
trading_view_figures = []

if __name__ == '__main__':

    def date_converter(sdate):
        return datetime.datetime.strptime(sdate, "%b %d %Y")

    ohlc = pd.read_csv(
        "data.csv",
        sep=";",
        thousands=",",
        decimal=".",
        dtype={"open": np.float64,
               "high": np.float64,
               "low": np.float64,
               "close": np.float64,
               "volume": np.int32
               },
        converters={"date": date_converter})

    sma20 = ohlc['close'].rolling(window=20).mean()
    sma50 = ohlc['close'].rolling(window=50).mean()
    sma100 = ohlc['close'].rolling(window=100).mean()

    plot_candlestick(ohlc, date_format='%b %d %Y')
    plot_line(sma20, name='SMA 20')
    plot_line(sma50, name='SMA 50')
    plot_line(sma100, name='SMA 100')
    plot_volume(ohlc['volume'])

    # figure()
    # plot_candlestick(ohlc.values, date_format='%b %d %Y')
    # plot_line(sma20.values)
    # plot_line(sma50.values)
    show()

    #plot(ohlc.values, sma20)

    print('asdasd')
