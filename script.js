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
        const lineChart = chart.addLineSeries({
            color: config.color,
            lineWidth: 2,
            priceLineVisible: false, //----------
            baseLineVisible: false,
            crosshairMarkerVisible: false,
            lastValueVisible: false
        });

        const setLegendText = (legend, priceValue) => {
            let val = 'n/a';
            if (priceValue !== undefined) {
                val = (Math.round(priceValue * 100) / 100).toFixed(2);
            }
            legend.innerHTML = `
                <div>
                    <p>
                        ${config.name}
                        <span style="color:${config.color}">${val}</span>
                    </p>
                </div>`;
        }

        const createLegentDiv = (lineIndex) => {
            var legend = document.createElement('div');
            legend.className = 'line-legend';
            legend.style.display = 'block';
            legend.style.left = 3 + 'px';
            legend.style.top = (1.5 * lineIndex) + 'em';
            return legend;
        };

        const legend = createLegentDiv(config.index)
        chartContainer.appendChild(legend);

        setLegendText(lineChart)

        chart.subscribeCrosshairMove((param) => {
            setLegendText(legend, param.seriesPrices.get(lineChart));
        });

        return lineChart;
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
                        createChartSeries(s.type, chart, s.config)
                            .setData(s.series);
                    });
            });
    });
})()