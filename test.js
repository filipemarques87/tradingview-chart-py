html,
body {
	font-family: 'Trebuchet MS', Roboto, Ubuntu, sans-serif;
	background: #f9fafb;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
}

.sma-legend {
	width: 96px;
	height: 70px;
	position: absolute;
	padding: 8px;
	font-size: 14px;
	background-color: rgba(255, 255, 255, 0.23);
	text-align: left;
	z-index: 1000;
	pointer-events: none;
}



---------------------- 


document.body.style.position = 'relative';

var container = document.createElement('div');
document.body.appendChild(container);

var width = 600;
var height = 300;

var chart = LightweightCharts.createChart(container, {
	width: width,
	height: height,
  crosshair: {
		mode: LightweightCharts.CrosshairMode.Normal,
	},
});

var candleSeries = chart.addCandlestickSeries();
var data = generateBarsData();
candleSeries.setData(data);

var smaData = calculateSMA(data, 10);
var smaLine = chart.addLineSeries({
	color: 'rgba(4, 111, 232, 1)',
	lineWidth: 2,
});
smaLine.setData(smaData);

var legend = document.createElement('div');
legend.className = 'sma-legend';
container.appendChild(legend);
legend.style.display = 'block';
legend.style.left = 3 + 'px';
legend.style.top = 3 + 'px';

setLegendText(legend, 'MA10')




var smaData50 = calculateSMA(data, 50);
console.log(smaData50)
var smaLine50 = chart.addLineSeries({
	color: 'rgba(4, 111, 0, 1)',
	lineWidth: 2,
});
smaLine50.setData(smaData50);

var legend50 = document.createElement('div');
legend50.className = 'sma-legend';
container.appendChild(legend50);
legend50.style.display = 'block';
legend50.style.left = 3 + 'px';
legend50.style.top = '2em';


setLegendText(legend50, 'MA50')



function setLegendText(legend, txt, priceValue) {
	let val = 'n/a';
	if (priceValue !== undefined) {
		val = (Math.round(priceValue * 100) / 100).toFixed(2);
	}
	legend.innerHTML = txt+' <span style="color:rgba(4, 111, 232, 1)">' + val + '</span>';
}


// setLegendText(smaData[smaData.length - 1].value);

chart.subscribeCrosshairMove((param) => {
	setLegendText(legend, 'MA10', param.seriesPrices.get(smaLine));
  //console.log(param.seriesPrices.get(smaLine50))
  setLegendText(legend50, 'MA50', param.seriesPrices.get(smaLine50));
});


function calculateSMA(data, count){
  var avg = function(data) {
    var sum = 0;
    for (var i = 0; i < data.length; i++) {
       sum += data[i].close;
    }
    return sum / data.length;
  };
  var result = [];
  for (var i=count - 1, len=data.length; i < len; i++){
    var val = avg(data.slice(i - count + 1, i));
    result.push({ time: data[i].time, value: val});
  }
  return result;
}

function generateBarsData(period) {
	var res = [];
	var controlPoints = generateControlPoints(res, period);
	for (var i = 0; i < controlPoints.length - 1; i++) {
		var left = controlPoints[i];
		var right = controlPoints[i + 1];
		fillBarsSegment(left, right, res);
	}
	return res;
}

function fillBarsSegment(left, right, points) {
	var deltaY = right.price - left.price;
	var deltaX = right.index - left.index;
	var angle = deltaY / deltaX;
	for (var i = left.index; i <= right.index; i++) {
		var basePrice = left.price + (i - left.index) * angle;
		var openNoise = (0.1 - Math.random() * 0.2) + 1;
		var closeNoise = (0.1 - Math.random() * 0.2) + 1;
		var open = basePrice * openNoise;
		var close = basePrice * closeNoise;
		var high = Math.max(basePrice * (1 + Math.random() * 0.2), open, close);
		var low = Math.min(basePrice * (1 - Math.random() * 0.2), open, close);
		points[i].open = open;
		points[i].high = high;
		points[i].low = low;
		points[i].close = close;
	}
}

function generateControlPoints(res, period, dataMultiplier) {
	var time = period !== undefined ? period.timeFrom : { day: 1, month: 1, year: 2018 };
	var timeTo = period !== undefined ? period.timeTo : { day: 1, month: 1, year: 2019 };
	var days = getDiffDays(time, timeTo);
	dataMultiplier = dataMultiplier || 1;
	var controlPoints = [];
	controlPoints.push({ index: 0, price: getRandomPrice() * dataMultiplier });
	for (var i = 0; i < days; i++) {
		if (i > 0 && i < days - 1 && Math.random() < 0.05) {
			controlPoints.push({ index: i, price: getRandomPrice() * dataMultiplier });
		}
		res.push({ time: time });
		time = nextBusinessDay(time);
	}
	controlPoints.push({ index: res.length - 1, price: getRandomPrice() * dataMultiplier });
	return controlPoints;
}

function getDiffDays(dateFrom, dateTo) {
	var df = convertBusinessDayToUTCTimestamp(dateFrom);
	var dt = convertBusinessDayToUTCTimestamp(dateTo);
	var diffTime = Math.abs(dt.getTime() - df.getTime());
	return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

function convertBusinessDayToUTCTimestamp(date) {
	return new Date(Date.UTC(date.year, date.month - 1, date.day, 0, 0, 0, 0));
}

function nextBusinessDay(time) {
	var d = convertBusinessDayToUTCTimestamp({ year: time.year, month: time.month, day: time.day + 1 });
	return { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate() };
}

function getRandomPrice() {
	return 10 + Math.round(Math.random() * 10000) / 100;
}