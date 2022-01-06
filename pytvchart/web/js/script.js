(() => {
    // html element that holds the chart
    const chartContainer = document.getElementById('chart-container');

    // creates the main chart object
    const createChart = (mainConfig) => {
        const chart = LightweightCharts.createChart(chartContainer, {
            width: 600,
            height: 400,
            layout: {
                background: {
                    color: mainConfig.backgroundColor,
                },
                textColor: mainConfig.textColor,
            },
            grid: {
                vertLines: {
                    color: mainConfig.gridColor,
                },
                horzLines: {
                    color: mainConfig.gridColor,
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: mainConfig.borderColor,
            },
            timeScale: {
                borderColor: mainConfig.borderColor,
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
        return chart.addCandlestickSeries({
            upColor: config.up_colour,
            downColor: config.down_colour,
            wickUpColor: config.wick_up_colour,
            wickDownColor: config.wick_down_colour,
        });
    };

    // creates line chart object
    const createLineChart = (chart, config) => {
        return chart.addLineSeries({
            color: config.colour,
            lineWidth: 2,
            priceLineVisible: false,
            baseLineVisible: false,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
        });
    };

    // creates volume chart object
    const createVolumeChart = (chart, config) => {
        return chart.addHistogramSeries({
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

    const addLegentToChart = (chart, mainConfig, lineChart, chartConfig) => {
        const setLegendText = (legend, priceValue) => {
            let val = 'n/a';
            const myColour = chartConfig.colour || mainConfig.textColor;
            if (priceValue !== undefined) {
                // candlestick case
                if (isNaN(priceValue)) {
                    keys = Object.keys(priceValue);
                    nextKeys = keys.slice(1);
                    val = nextKeys.reduce(
                        (p, c) => `${p}, ${c}: ${priceValue[c]}`,
                        `${keys[0]}: ${priceValue[keys[0]]}`)
                } else {
                    // line, volume case
                    val = (Math.round(priceValue * 100) / 100).toFixed(2);
                }
            }

            legend.innerHTML = `
                <div>
                    <p>
                        <span style="color:${mainConfig.textColor}">${chartConfig.name}</span>
                        <span style="color:${myColour}">${val}</span>
                    </p>
                </div>`;
        }

        const createLegentDiv = (lineIndex) => {
            var legend = document.createElement('div');
            legend.className = 'line-legend';
            legend.style.top = (1.5 * lineIndex) + 'em';
            return legend;
        };

        const legend = createLegentDiv(chartConfig.legend_index)
        chartContainer.appendChild(legend);

        setLegendText(legend)

        chart.subscribeCrosshairMove((param) => {
            setLegendText(legend, param.seriesPrices.get(lineChart));
        });
    };

    window.addEventListener('pywebviewready', () => {
        pywebview.api.request_data()
            .then((response) => {
                const mainConfig = JSON.parse(response.config);
                const chart = createChart(mainConfig);

                response.series
                    .map(s => JSON.parse(s))
                    .forEach((s, i) => {
                        const subChart = createChartSeries(s.type, chart, s.config)
                        subChart.setData(s.series);
                        if (s.config.show_legend) {
                            addLegentToChart(chart, mainConfig, subChart, s.config);
                        }

                        // adds the markers to the first chart
                        if (i === 0) {
                            subChart.setMarkers(response.events.map(s => JSON.parse(s)));
                        }
                    });
            });
    });
})()