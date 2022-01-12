# tradingview-chart-py
Python wrapper to plot candlestick data using tradingview lightweight charts

## Example
```python
import pytvchart as tvc

# plots a candlestick series
tvc.plot_candlestick(ohlc, name='BTCUSDT', date_format='%b %d %Y')

# plots a line series
tvc.plot_line(sma20, name='SMA 20')

# plots another line series
tvc.plot_line(sma100, name='SMA 100')

# plots volume data
tvc.plot_volume(ohlc['volume'])

# plots an event
tvc.plot_event('Dec 02 2011', '314', type='sell')

# plots another event
tvc.plot_event('Sep 14 2011', '366', type='buy')

```

![figure-1](/figure-1.png)

