(() => {
    // html element that holds the chart
    const chartContainer = document.getElementById('chart-container');

    // creates the main chart object
    const createChart = (config) => {
        const chart = LightweightCharts.createChart(chartContainer, {
            width: 600,
            height: 400,
            layout: {
                backgroundColor: config.backgroundColor,
                textColor: config.textColor,
            },
            grid: {
                vertLines: {
                    color: config.gridColor,
                },
                horzLines: {
                    color: config.gridColor,
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: config.borderColor,
            },
            timeScale: {
                borderColor: config.borderColor,
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
            test: 'filipe'
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

    const addLegentToChart = (chart, config, lineChart, subChartConfig) => {
        console.log(lineChart)
        const setLegendText = (legend, priceValue, lineChart2) => {

            let val = 'n/a';
            const myColour = lineChart['qe']['ki']['color'];
            if (priceValue !== undefined) {
                if (isNaN(priceValue)) {
                    keys = Object.keys(priceValue);
                    nextKeys = keys.slice(1);
                    val = nextKeys.reduce(
                        (p, c) => `${p}, ${c}: ${priceValue[c]}`,
                        `${keys[0]}: ${priceValue[keys[0]]}`)
                } else {
                    val = (Math.round(priceValue * 100) / 100).toFixed(2);
                }
            }
            legend.innerHTML = `
                <div>
                    <p>
                        <span style="color:${config.textColor}">${subChartConfig.name}</span>
                        <span style="color:${myColour}">${val}</span>
                    </p>
                </div>`;
                //<span style="color:${subChartConfig.colour}">${val}</span>
        }

        const createLegentDiv = (lineIndex) => {
            var legend = document.createElement('div');
            legend.className = 'line-legend';
            legend.style.top = (1.5 * lineIndex) + 'em';
            return legend;
        };

        const legend = createLegentDiv(subChartConfig.legend_index)
        chartContainer.appendChild(legend);

        setLegendText(lineChart)

        chart.subscribeCrosshairMove((param) => {
            setLegendText(legend, param.seriesPrices.get(lineChart), lineChart);
        });
    };

    window.addEventListener('pywebviewready', () => {
        pywebview.api.request_data()
            .then((response) => {
                const config = JSON.parse(response.config);
                const chart = createChart(config);

                response.series
                    .map(s => JSON.parse(s))
                    .forEach((s, i) => {
                        const subChart = createChartSeries(s.type, chart, s.config)
                        subChart.setData(s.series);
                        if (s.config.show_legend) {
                            addLegentToChart(chart, config, subChart, s.config);
                        }

                        // adds the markers to the first chart
                        if (i === 0) {
                            subChart.setMarkers(response.events.map(s => JSON.parse(s)));
                        }
                    });
            });
    });
})()