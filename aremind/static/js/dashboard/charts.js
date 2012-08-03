google.load('visualization', '1', { packages: ['corechart'] });

ko.bindingHandlers.satisfaction_piechart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            var options = {
                vAxis: {
                    textPosition: 'in'
                },
                chartArea: {
                    top: 10,
                    left: 0,
                    width: '100%'
                }
            };

            element.wrapper = new google.visualization.ChartWrapper({
                chartType: 'PieChart',
                options: options,
                containerId: $(element).attr('id')
            });

            var active = ko.utils.unwrapObservable(valueAccessor());

            if(active) {
                // Add the data to the chart and then draw it
                var dataTable = google.visualization.arrayToDataTable([
                    ['Category', ''],
                    ['Satisfied', active.data.satisfaction.True],
                    ['Unsatisfied', active.data.satisfaction.False]
                ]);
                element.wrapper.setDataTable(dataTable);
                element.wrapper.draw();
            }
        });
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        if (!element.wrapper || !active) {
            return;
        }

        var dataTable = google.visualization.arrayToDataTable([
            ['Category', ''],
            ['Satisfied', active.data.satisfaction.True],
            ['Unsatisfied', active.data.satisfaction.False]
        ]);
        element.wrapper.setDataTable(dataTable);
        element.wrapper.draw();
    }
};

ko.bindingHandlers.pbf_category_barchart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            var options = {
                vAxis: {
                    textPosition: 'left'
                },
                chartArea: {
                    top: 0,
                    left: 110,
                    width: '90%'
                }
            };

            element.wrapper = new google.visualization.ChartWrapper({
                chartType: 'BarChart',
                options: options,
                containerId: $(element).attr('id')
            });

            var bar_clicked = function() {
                var opt = element.wrapper.getChart().getSelection()[0].row;
                var metric = ['wait', 'friendly', 'pricedisp', 'drugavail', 'clean'][opt];
                window.location.href = '/dashboard/pbf/reports/?metric=' + metric;
            };

            google.visualization.events.addListener(element.wrapper, 'select', bar_clicked);

            var active = ko.utils.unwrapObservable(valueAccessor());

            if(active) {
                // Add the data to the chart and then draw it
                var dataTable = google.visualization.arrayToDataTable([
                    ['Category', ''],
                    ['Waiting Time', active.data.by_category.waiting_time],
                    ['Staff Friendliness', active.data.by_category.staff_friendliness],
                    ['Price Display', active.data.by_category.price_display],
                    ['Drug Availability', active.data.by_category.drug_availability],
                    ['Cleanliness & Hygiene', active.data.by_category.cleanliness]
                ]);
                element.wrapper.setDataTable(dataTable);
                element.wrapper.draw();
            }
        });
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        if (!element.wrapper || !active) {
            return;
        }

        var dataTable = google.visualization.arrayToDataTable([
            ['Category', ''],
            ['Waiting Time', active.data.by_category.waiting_time],
            ['Staff Friendliness', active.data.by_category.staff_friendliness],
            ['Price Display', active.data.by_category.price_display],
            ['Drug Availability', active.data.by_category.drug_availability],
            ['Cleanliness & Hygiene', active.data.by_category.cleanliness]
        ]);
        element.wrapper.setDataTable(dataTable);
        element.wrapper.draw();
    }
};

ko.bindingHandlers.fadama_category_barchart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            var options = {
                vAxis: {
                    textPosition: 'left'
                },
                chartArea: {
                    top: 0,
                    left: 110,
                    width: '90%'
             }
            };

            element.wrapper = new google.visualization.ChartWrapper({
                chartType: 'BarChart',
                options: options,
                containerId: $(element).attr('id')
            });

            var bar_clicked = function() {
                var opt = element.wrapper.getChart().getSelection()[0].row;
                var metric = ['serviceprovider', 'people', 'land', 'info', 'ldp', 'financial'][opt];
                window.location.href = '/dashboard/fadama/reports/?metric=' + metric;
            };

            google.visualization.events.addListener(element.wrapper, 'select', bar_clicked);

            var active = ko.utils.unwrapObservable(valueAccessor());

            if(active) {
                var dataTable = google.visualization.arrayToDataTable([
                    ['Category', ''],
                    ['Service Providers', active.data.by_category.serviceprovider],
                    ['People from Fadama', active.data.by_category.people],
                    ['Land Issues', active.data.by_category.land],
                    ['Information Issues', active.data.by_category.info],
                    ['LDP Approval', active.data.by_category.ldp],
                    ['Financial Issues', active.data.by_category.financial]
                ]);
                element.wrapper.setDataTable(dataTable);
                element.wrapper.draw();
            }
        });
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        if (!element.wrapper || !active) {
            return;
        }

        var dataTable = google.visualization.arrayToDataTable([
            ['Category', ''],
            ['Service Providers', active.data.by_category.serviceprovider],
            ['People from Fadama', active.data.by_category.people],
            ['Land Issues', active.data.by_category.land],
            ['Information Issues', active.data.by_category.info],
            ['LDP Approval', active.data.by_category.ldp],
            ['Financial Issues', active.data.by_category.financial]
        ]);
        element.wrapper.setDataTable(dataTable);
        element.wrapper.draw();
    }
};

ko.bindingHandlers.pbf_current_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        var metric = viewModel.active_metric();
        if (!element.charts_init || !active || !metric || metric == 'all') {
            return;
        }

        var options = {
            vAxis: {
                textPosition: 'in'
            },
            chartArea: {
                top: 10,
                left: 0,
                width: '100%'
            }
        };

        var ordering = ['True', 'False', '<2', '2-4', '>4'];

        var data = [['Category', '']];
        var raw_data = monthly_datapoints(active, metric);
        $.each(ordering, function(i, e) {
            if (raw_data[e] != null) {
                data.push([get_pbf_caption(metric, e), raw_data[e]]);
            }
        });

        var chart_type = null;
        if (metric == 'wait') {
            chart_type = 'ColumnChart';
        } else {
            chart_type = 'PieChart';
        }

        var chart = new google.visualization[chart_type](element);
        chart.draw(google.visualization.arrayToDataTable(data), options);
    }
};

ko.bindingHandlers.pbf_historical_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        var metric = viewModel.active_metric();
        if (!element.charts_init || !active || !metric || metric == 'all') {
            return;
        }

        var options = {
            vAxis: {
                textPosition: 'in'
            },
            chartArea: {
                top: 10,
                left: 0,
                width: '85%'
            },
        };

        var FUZZ = 2;
        var curmonthix = viewModel.monthly.indexOf(active);
        var minmonthix = curmonthix - 2;
        var maxmonthix = curmonthix + 2;

        var ordering = null;
        if (metric == 'wait') {
            ordering = ['<2', '2-4', '>4'];
        } else {
            ordering = ['True', 'False'];
        }

        var labels = ['Month'];
        var raw_data = monthly_datapoints(active, metric);
        $.each(ordering, function(i, e) {
            labels.push(get_pbf_caption(metric, e));
        });
        var data = [labels];

        for (var i = minmonthix; i <= maxmonthix; i++) {
            var row = [];
            if (i < 0 || i >= viewModel.monthly().length) {
                row.push('');
                for (var j = 1; j < labels.length; j++) {
                    row.push(null);
                }
            } else {
                var m = viewModel.monthly()[i];
                raw_data = monthly_datapoints(m, metric);
                row.push(m.month_label());
                $.each(ordering, function(i, e) {
                    row.push(raw_data[e] || 0);
                });
            }
            data.push(row);
        }

        var chart = new google.visualization.ColumnChart(element);
        chart.draw(google.visualization.arrayToDataTable(data), options);
    }
};

ko.bindingHandlers.fadama_current_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        var metric = viewModel.active_metric();
        if (!element.charts_init || !active || !metric || metric == 'all') {
            return;
        }

        var options = {
            vAxis: {
                textPosition: 'in'
            },
            chartArea: {
                top: 10,
                left: 0,
                width: '100%'
            }
        };

        var ordering = ['True', 'False', '<2', '2-4', '>4'];

        var data = [['Category', '']];
        var raw_data = monthly_datapoints(active, metric);

        $.each(get_fadama_ordering(metric), function(i, e) {
            data.push([get_fadama_caption(metric, e), raw_data[e] || 0]);
        });

        var chart_type = 'PieChart';

        var chart = new google.visualization[chart_type](element);
        chart.draw(google.visualization.arrayToDataTable(data), options);

        var bar_clicked = function() {
            if (chart.getSelection().length === 0) {
                return;
            }

            var opt = chart.getSelection()[0].row;
            var subcat = viewModel.subcategories()[opt + 1]; // the first is 'all', so offset by 1
            viewModel.active_subcategory(subcat);
        };

        google.visualization.events.addListener(chart, 'select', bar_clicked);
    }
};

ko.bindingHandlers.fadama_historical_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        var metric = viewModel.active_metric();
        if (!element.charts_init || !active || !metric || metric == 'all') {
            return;
        }

        var options = {
            vAxis: {
                textPosition: 'in'
            },
            chartArea: {
                top: 10,
                left: 0,
                width: '85%'
            }
        };

        var FUZZ = 2;
        var curmonthix = viewModel.monthly.indexOf(active);
        var minmonthix = curmonthix - 2;
        var maxmonthix = curmonthix + 2;

        var labels = ['Month'];
        var raw_data = monthly_datapoints(active, metric);
        $.each(get_fadama_ordering(metric), function(i, e) {
            labels.push(get_fadama_caption(metric, e));
        });
        var data = [labels];

        for (var i = minmonthix; i <= maxmonthix; i++) {
            var row = [];
            if (i < 0 || i >= viewModel.monthly().length) {
                row.push('');
                for (var j = 1; j < labels.length; j++) {
                    row.push(null);
                }
            } else {
                var m = viewModel.monthly()[i];
                raw_data = monthly_datapoints(m, metric);
                row.push(m.month_label());
                $.each(get_fadama_ordering(metric), function(i, e) {
                    row.push(raw_data[e] || 0);
                });
            }
            data.push(row);
        }

        var chart = new google.visualization.ColumnChart(element);
        chart.draw(google.visualization.arrayToDataTable(data), options);

        var bar_clicked = function() {
            if (chart.getSelection().length === 0) {
                return;
            }

            var opt = chart.getSelection()[0].column;
            var subcat = viewModel.subcategories()[opt]; // the first is 'all', so don't offset by 1
            viewModel.active_subcategory(subcat);
        };

        google.visualization.events.addListener(chart, 'select', bar_clicked);
    }
};