'use strict';

/* jshint globalstrict: true */
/* global dc,d3,crossfilter,colorbrewer */

var shopChart = dc.pieChart("#shopChart");
var quarterChart = dc.pieChart("#quarter-chart");
var dayOfWeekChart = dc.rowChart("#day-of-week-chart");
var moveChart = dc.lineChart("#monthly-move-chart");
var volumeChart = dc.barChart("#monthly-volume-chart");

$.getJSON("/rest/expenses/all.json", function (data) {
    /* since its a csv file we need to format the data a bit */
    var dateFormat = d3.time.format("%Y-%m-%d");
    var numberFormat = d3.format(".2f");

    data.forEach(function (d) {
        d.dd = dateFormat.parse(d.date);
        d.month = d3.time.month(d.dd); // pre-calculate month for better performance
        d.day = d3.time.day(d.dd); // pre-calculate month for better performance
        d.total = +d.total; // coerce to number
    });

    console.log(data);
    //### Create Crossfilter Dimensions and Groups
    //See the [crossfilter API](https://github.com/square/crossfilter/wiki/API-Reference) for reference.
    var ndx = crossfilter(data);
    var all = ndx.groupAll();

    // dimension by year
    var yearlyDimension = ndx.dimension(function (d) {
        return d3.time.year(d.dd).getFullYear();
    });
    // maintain running tallies by year as filters are applied or removed
    var yearlyPerformanceGroup = yearlyDimension.group().reduce(
        /* callback for when data is added to the current filter results */
        function (p, v) {
            ++p.count;
            p.totals += v.total;
            p.avgIndex = p.totals / p.count;
            return p;
        },
        /* callback for when data is removed from the current filter results */
        function (p, v) {
            --p.count;
            p.totals -= v.total;
            p.avgIndex = p.totals / p.count;
            return p;
        },
        /* initialize p */
        function () {
            return {count: 0, totals: 0, avgIndex: 0};
        }
    );

    // dimension by full date
    var dateDimension = ndx.dimension(function (d) {
        return d.dd;
    });

    // dimension by month
    var moveMonths = ndx.dimension(function (d) {
        return d.day;
    });
    // group by total movement within month
    var monthlyMoveGroup = moveMonths.group().reduceSum(function (d) {
        return d.total;
    });

    var indexAvgByMonthGroup = moveMonths.group().reduce(
        function (p, v) {
            ++p.days;
            p.total += v.total;
            p.avg = Math.round(p.total / p.days);
            return p;
        },
        function (p, v) {
            --p.days;
            p.total -= v.total;
            p.avg = p.days ? Math.round(p.total / p.days) : 0;
            return p;
        },
        function () {
            return {days: 0, total: 0, avg: 0};
        }
    );

    // summarize by shop
    var shop = ndx.dimension(function(d) {
        return d.shop;
    });

    var shopGroup = shop.group().reduceSum(function(d) {
        return d.total;
    });

    // summarize total by months
    var quarter = ndx.dimension(function (d) {
        var month = d.dd.getMonth();
        return d3.time.format("%B")(d.dd);
    });
    var quarterGroup = quarter.group().reduceSum(function (d) {
        return d.total;
    });

    // counts per weekday
    var dayOfWeek = ndx.dimension(function (d) {
        var day = d.dd.getDay();
        var name=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
        return day+"."+name[day];
     });
    var dayOfWeekGroup = dayOfWeek.group().reduceSum(function (d) {
        return d.total;
    });


    shopChart
        .width(320) // (optional) define chart width, :default = 200
        .height(320) // (optional) define chart height, :default = 200
        .radius(125) // define pie radius
        .dimension(shop) // set dimension
        .group(shopGroup) // set group
        /* (optional) by default pie chart will use group.key as it's label
         * but you can overwrite it with a closure */
//        .label(function (d) {
//            if (shopChart.hasFilter() && !shopChart.hasFilter(d.key))
//                return d.key + "(0%)";
//            return d.key + "(" + Math.floor(d.value / all.value() * 100) + "%)";
//        })
/*
        // (optional) whether chart should render labels, :default = true
        .renderLabel(true)
        // (optional) if inner radius is used then a donut chart will be generated instead of pie chart
        .innerRadius(40)
        // (optional) define chart transition duration, :default = 350
        .transitionDuration(500)
        // (optional) define color array for slices
        .colors(['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#dadaeb'])
        // (optional) define color domain to match your data domain if you want to bind data or color
        .colorDomain([-1750, 1644])
        // (optional) define color value accessor
        .colorAccessor(function(d, i){return d.value;})
        */;

    quarterChart.width(320)
        .height(320)
        .radius(125)
        .innerRadius(30)
        .dimension(quarter)
        .group(quarterGroup);

    //#### Row Chart
    dayOfWeekChart.width(320)
        .height(250)
        .margins({top: 60, left: 10, right: 10, bottom: 20})
        .group(dayOfWeekGroup)
        .dimension(dayOfWeek)
        // assign colors to each value in the x scale domain
        .colors(d3.scale.ordinal().range(['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#dadaeb']))
        .label(function (d) {
            return d.key.split(".")[1];
        })
        // title sets the row text
        .title(function (d) {
            return d.value;
        })
        .elasticX(true)
        .xAxis().ticks(4);

    //#### Stacked Area Chart
    //Specify an area chart, by using a line chart with `.renderArea(true)`
    moveChart
        .renderArea(true)
        .width(990)
        .height(200)
        .transitionDuration(1000)
        .margins({top: 30, right: 50, bottom: 25, left: 40})
        .dimension(moveMonths)
        .mouseZoomable(true)
        // Specify a range chart to link the brush extent of the range with the zoom focue of the current chart.
        .rangeChart(volumeChart)
        .x(d3.time.scale().domain([new Date(2013, 0, 1), new Date(2013, 9, 31)]))
        .round(d3.time.month.round)
        .xUnits(d3.time.months)
        .elasticY(true)
        .renderHorizontalGridLines(true)
        .legend(dc.legend().x(800).y(10).itemHeight(13).gap(5))
        .brushOn(false)
        // Add the base layer of the stack with group. The second parameter specifies a series name for use in the legend
        // The `.valueAccessor` will be used for the base layer
        .group(indexAvgByMonthGroup, "Average amount spent at each shopping")
        .valueAccessor(function (d) {
            return d.value.avg;
        })
        // stack additional layers with `.stack`. The first paramenter is a new group.
        // The second parameter is the series name. The third is a value accessor.
        .stack(monthlyMoveGroup, "Total spent shopping", function (d) {
            return d.value;
        })
        // title can be called by any stack layer.
        .title(function (d) {
            console.log(d)
            var value = d.data.value.avg ? d.data.value.avg : d.data.value;
            if (isNaN(value)) value = 0;
            return dateFormat(d.x) + "\n" + numberFormat(value);
        });

    volumeChart.width(990)
        .height(40)
        .margins({top: 0, right: 50, bottom: 20, left: 40})
        .dimension(moveMonths)
        .group(monthlyMoveGroup)
        .centerBar(true)
        .gap(1)
        .x(d3.time.scale().domain([new Date(2012, 0, 1), new Date(2013, 11, 31)]))
        .round(d3.time.month.round)
        .xUnits(d3.time.months);

    dc.dataCount(".dc-data-count")
        .dimension(ndx)
        .group(all);

    dc.dataTable(".dc-data-table")
        .dimension(dateDimension)
        // data table does not use crossfilter group but rather a closure
        // as a grouping function
        .group(function (d) {
            var format = d3.format("02d");
            return d.dd.getFullYear() + "/" + format((d.dd.getMonth() + 1));
        })
        .size(10) // (optional) max number of records to be shown, :default = 25
        // dynamic columns creation using an array of closures
        .columns([
            function (d) {
                return d.date;
            },
            function (d) {
                return numberFormat(d.total);
            },
            function (d) {
                return d.shop;
            }
        ])
        // (optional) sort using the given field, :default = function(d){return d;}
        .sortBy(function (d) {
            return d.dd;
        })
        // (optional) sort order, :default ascending
        .order(d3.ascending)
        // (optional) custom renderlet to post-process chart using D3
        .renderlet(function (table) {
            table.selectAll(".dc-table-group").classed("info", true);
        });


    dc.renderAll();
});

