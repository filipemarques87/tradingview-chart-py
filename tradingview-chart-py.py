from numpy.lib.shape_base import tile
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


class TradingViewMarker:
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

    def __init__(self, ohlc_series, title=''):
        self.series = [ohlc_series]
        self.markers = []
        self.title = title

    def add_series(self, series):
        ''' Adds a new series to this figure '''
        self.series.append(series)

    def add_marker(self, marker):
        self.markers.append(marker)

    def serialize(self):
        return {
            'series': [s.serialize() for s in self.series],
            'markers': [s.serialize() for s in self.markers]
        }
        


class WebviewApi:
    def __init__(self, figure):
        ''' Class used to communiate between python code and tradingview char library '''
        self.figure = figure

    # def _parse_user_config(self, **kwargs):
    #     ''' Parses the user configurations and save those options in ChartConfig object '''
    #     chart_config = ChartConfig()
    #     for field in fields(ChartConfig):
    #         if field.name in kwargs:
    #             setattr(chart_config, field.name, kwargs[field.name])

    #     return chart_config

    def request_data(self):
        response = {
            'series': self.figure.serialize(),
            #'markers': self.figure.serialize()

            #'config': json.dumps(dataclasses.asdict(self.chart_cofig))
        }
        return self.figure.serialize() # response


def plot_candlestick(np_ohlc_series, name='', date_format=None, show_legend=True):
    ''' Plots candlestick data '''
    global current_figure_index
    global trading_view_figures

    ohlc_series = util.convert_series(np_ohlc_series)

    if current_figure_index < len(trading_view_figures):
        raise ValueError(
            f'Cannot add a candle stick serie. Figure {current_figure_index} already exists')

    ignore, ncolumns = np.shape(ohlc_series)
    if ncolumns < 5:
        raise ValueError(
            f'Expect 5 columns: time, open, high, low, close but got {ncolumns}')

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

    trading_view_figures.append(TradingViewFigure(
        TradingViewSeries(ohlc_series, 'ohlc', name=name, show_legend=show_legend, legend_index=0, date_format=date_format)))


def plot_line(np_line_series, name=None, colour=None, show_legend=True):
    ''' Adds a plot into candlestick chart '''
    global current_figure_index
    global trading_view_figures

    if current_figure_index >= len(trading_view_figures):
        raise ValueError(f'Figure {current_figure_index} does not exists')

    current_figure = trading_view_figures[current_figure_index]
    line_series = util.convert_series(np_line_series)
    ohlc_series = current_figure.series[0].series

    if len(np.shape(line_series)) != 1:
        raise ValueError(
            f'Expect 1 column but got {len(line_series.shape)}')

    if len(line_series) != len(ohlc_series):
        raise ValueError(
            f'Line lenght and candle stick length are different: {len(line_series)} != {len(ohlc_series)}')

    line_series = [{
        'time': row[0]['time'],
        'value': row[1]}
        for row in zip(ohlc_series, line_series) if not np.isnan(row[1])]

    # get correct line color if not set
    if colour is None:
        index = len(
            [s for s in current_figure.series if s.type == 'line'])
        colour = COLOR_PALLET[index % len(COLOR_PALLET)]

    legend_index = len([s for s in current_figure.series if s.config['show_legend']])
    
    if name is None:
        name = f'Line {index + 1}'
    current_figure.add_series(TradingViewSeries(line_series, 'line', name=name, colour=colour, show_legend=show_legend, legend_index=legend_index))


def plot_volume(np_volume_series, name='Vol', colour_up='rgba(0, 150, 136, 0.8)', colour_down='rgba(255,82,82, 0.8)', show_legend=True):
    ''' Adds volume into candlestick chart '''
    global current_figure_index
    global trading_view_figures

    if current_figure_index >= len(trading_view_figures):
        raise ValueError(f'Figure {current_figure_index} does not exists')

    current_figure = trading_view_figures[current_figure_index]
    volume_series = util.convert_series(np_volume_series)
    ohlc_series = current_figure.series[0].series

    if len(np.shape(volume_series)) != 1:
        raise ValueError(
            f'Expect 1 column but got {len(np.shape(volume_series))}')

    if len(volume_series) != len(ohlc_series):
        raise ValueError(
            f'Line lenght and candle stick length are different: {len(volume_series)} != {len(ohlc_series)}')

    volume_series = [{
        'time': row[0]['time'],
        'value': row[1],
        'color': colour_up if row[0]['open'] < row[0]['close'] else colour_down}
        for row in zip(ohlc_series, volume_series) if not np.isnan(row[1])]
    
    legend_index = len([s for s in current_figure.series if s.config['show_legend']])

    current_figure.add_series(TradingViewSeries(
        volume_series, 'volume', name=name, show_legend=show_legend, legend_index=legend_index))


def plot_marker(time, text, type=None, position='aboveBar', shape='arrowDown', color='#000'):
    

    if position not in (None,'', 'aboveBar', 'belowBar','inBar'):
        raise ValueError

    if shape not in (None, '', 'circle', 'square', 'arrowUp', 'arrowDown'):
        raise ValueError

    if type not in (None, '', 'sell', 'buy'):
        raise ValueError

    if type == 'sell':
        position, color, shape, text = 'aboveBar',  '#e91e63', 'arrowDown', f'Sell @ {text}'
    elif type == 'buy':
        position, color, shape, text = 'belowBar',  '#2196F3', 'arrowUp', f'Buy @ {text}'

    current_figure = trading_view_figures[current_figure_index]
    date_format = current_figure.series[0].config['date_format']

    if date_format is not None:
        time = int(datetime.datetime.strptime(time, date_format).timestamp())

    current_figure.add_marker(TradingViewMarker(time, text, position, shape, color))


def show():
    ''' Shows the chart '''
    global trading_view_figures

    for idx, figure in enumerate(trading_view_figures):
        title = figure.title or f'Figure {idx + 1}'
        webview_api = WebviewApi(figure)
        window = webview.create_window(
            title, 'index.html', js_api=webview_api)
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

    a=len(sma20) * [275]
    plot_candlestick(ohlc, name='BTCUSDT', date_format='%b %d %Y')
    #plot_line(sma20, name='SMA 20')
    #plot_line(sma50)
    #plot_line(a, name='SMA 10', show_legend=False)
    #plot_line(sma100, name='SMA 100')
    #plot_volume(ohlc['volume'])
    #plot_marker('Dec 02 2011', '314', type='sell')
    #plot_marker('Sep 14 2011', '366', type='buy')
    #plot_marker('Sep 07 2011', 'outras cenas')
    #plot_marker('Jan 04 2010', 'outras cenas')

    # figure()
    # plot_candlestick(ohlc.values, date_format='%b %d %Y')
    # plot_line(sma20.values)
    # plot_line(sma50.values)

    show()

    #plot(ohlc.values, sma20)

    print('asdasd')
