import webview
import json
from dataclasses import dataclass, fields
import datetime
import pandas as pd
import numpy as np


class TradingViewSeries:
    '''
    This class holds informations for a single series to be shown in the figure.
    I can be a candle stick series, a line series, volume series, ...
    '''

    def __init__(self, series, type):
        self.series = series
        self.type = type

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


@dataclass
class ChartConfig:
    ''' Chart configuration to pass to tradingview chart library '''
    show_candlestick: bool = True
    show_volume: bool = True
    volume_colour_up: str = 'rgba(0, 150, 136, 0.8)'
    volume_colour_down: str = 'rgba(255,82,82, 0.8)'


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

    def _validate_data(ohlc_series):
        ''' Validates the candle stick data '''
        if not isinstance(ohlc_series, np.ndarray):
            raise ValueError('Candle stick data must be a numpy ndarray')

        ignore, ncolumns = ohlc_series.shape
        if ncolumns < 5:
            raise ValueError(
                f'Expect 5 columns: time, open, high, low, close but got {ncolumns}')

    def _convert_date(ohlc_series, date_format):
        ''' Converts the column date to timestamp '''
        if date_format is not None:
            for row in ohlc_series:
                row[0] = int(datetime.datetime.strptime(
                    row[0], date_format).timestamp())
        return ohlc_series

    def _prepare_data_for_trading_view_library(ohlc_series):
        ''' Prepare the data to be used in TradingView library '''
        return [{
            'time': row[0],
            'open': row[1],
            'high': row[2],
            'low': row[3],
            'close': row[4]}
            for row in ohlc_series]

    if current_figure_index < len(trading_view_figures):
        raise ValueError(
            f'Cannot add a candle stick serie. Figure {current_figure_index} already exists')

    ohlc_series = np_ohlc_series
    _validate_data(ohlc_series)
    ohlc_series = _convert_date(ohlc_series, kwargs['date_format'])
    ohlc_series = _prepare_data_for_trading_view_library(ohlc_series)

    trading_view_figures.append(TradingViewFigure(
        TradingViewSeries(ohlc_series, 'ohlc')))


def plot_line(np_line_series, **kwargs):
    ''' Adds a plot into candlestick chart '''
    global current_figure_index
    global trading_view_figures

    def _validate_data(line_series, ohcl_series):
        ''' Validates the candle stick data '''
        if not isinstance(line_series, np.ndarray):
            raise ValueError('Candle stick data must be a numpy ndarray')

        if len(line_series.shape) != 1:
            raise ValueError(
                f'Expect 1 column but got {len(line_series.shape)}')

        if line_series.shape[0] != len(ohcl_series):
            raise ValueError(
                f'Line lenght and candle stick length are different: {line_series.shape[0]} != {ohcl_series.shape[0]}')

    def _prepare_data_for_trading_view_library(line_series, ohlc_series):
        return [{'time': row[0]['time'], 'value': row[1]}
                for row in zip(ohlc_series, line_series) if not np.isnan(row[1])]

    if current_figure_index >= len(trading_view_figures):
        raise ValueError(f'Figure {current_figure_index} does not exists')

    current_figure = trading_view_figures[current_figure_index]
    line_series = np_line_series
    ohlc_series = current_figure.series[0].series
    _validate_data(line_series, ohlc_series)
    line_series = _prepare_data_for_trading_view_library(
        line_series, ohlc_series)

    current_figure.add_series(TradingViewSeries(line_series, 'line'))


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

    plot_candlestick(ohlc.values, date_format='%b %d %Y')
    plot_line(sma20.values)
    plot_line(sma50.values)
    

    figure()
    plot_candlestick(ohlc.values, date_format='%b %d %Y')
    plot_line(sma20.values)
    plot_line(sma50.values)
    show()

    #plot(ohlc.values, sma20)

    print('asdasd')
