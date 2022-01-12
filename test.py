import datetime
import pandas as pd
import numpy as np

import pytvchart as tvc



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

    a = len(sma20) * [275]


    tvc.plot_candlestick(ohlc, name='BTCUSDT', date_format='%b %d %Y')
    tvc.plot_line(sma20, name='SMA 20')
    tvc.plot_line(sma50)
    tvc.plot_line(a, name='SMA 10', show_legend=True)
    tvc.plot_line(sma100, name='SMA 100')
    tvc.plot_volume(ohlc['volume'])
    tvc.plot_event('Dec 02 2011', '314', type='sell')
    tvc.plot_event('Sep 14 2011', '366', type='buy')
    tvc.plot_event('Sep 07 2011', 'outras cenas')
    tvc.plot_event('Jan 04 2010', 'outras cenas')

    tvc.figure(theme='dark')
    tvc.plot_candlestick(ohlc.values, date_format='%b %d %Y')
    tvc.plot_line(sma20.values)
    tvc.plot_line(sma50.values)
    tvc.plot_event('Dec 02 2011', '314', type='sell',size=3)
    tvc.plot_event('Sep 14 2011', '366', type='buy')
    tvc.plot_event('Sep 07 2011', 'outras cenas')
    tvc.plot_event('Jan 04 2010', 'outras cenas')


    tvc.show()
