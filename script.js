(() => {
    // html element that holds the chart
    const chartContainer = document.getElementById('chart-container');

    // creates the main chart object
    const createChart = (config) => {
        const chart = LightweightCharts.createChart(chartContainer, {
            width: 600,
            height: 400,
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal
            }
        });

        // used to fit the chart area into view area
        new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== chartContainer) {
                return;
            }
            const newRect = entries[0].contentRect;
            chart.applyOptions({ height: newRect.height, width: newRect.width });
        }).observe(chartContainer)

        return chart;
    };

    // creates candle stick chart object
    const createCandleStickChart = (chart, config) => {
        return chart.addCandlestickSeries();
    };

    // creates line chart object
    const createLineChart = (chart, config) => {
        return chart.addLineSeries({
            color: 'rgba(4, 111, 232, 1)',
            lineWidth: 2,
            priceLineVisible: false, //----------
            baseLineVisible: false,
            crosshairMarkerVisible: false,
            lastValueVisible: false
        });
    };

    // creates volume chart object
    const createVolumeChart = (chart, config) => {
        return chart.addHistogramSeries({
            // color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
    };

    const extractVolumeData = (data, config) => {
        return data.map((d) => {
            return {
                'time': d.time,
                'value': d.volume,
                'color': d.open < d.close
                    ? config.volume_colour_up
                    : config.volume_colour_down
            }
        });
    };


    const createChartSeries = (type, chart, config) => {
        if (type === 'ohlc') {
            return createCandleStickChart(chart, config);
        } else if (type === 'line') {
            return createLineChart(chart, config);
        } else if (type === 'volume') {
            return createVolumeChart(chart, config);
        }
        throw new TypeError('Type not supported')
    }

    window.addEventListener('pywebviewready', () => {
        pywebview.api.request_data()
            .then((response) => {
                const config = {};//JSON.parse(response.config);
                const chart = createChart(config);

                response.series
                    .map(s => JSON.parse(s))
                    .forEach(s => {
                        createChartSeries(s.type, chart, config)
                            .setData(s.series);
                    });
            });
    });
})()