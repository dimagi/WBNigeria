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
	category_barchart_init(element, valueAccessor, 'pbf', pbf_categories);
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	category_barchart_update(element, valueAccessor, pbf_categories);
    }
};

ko.bindingHandlers.fadama_category_barchart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	category_barchart_init(element, valueAccessor, 'fadama', fadama_categories);
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	category_barchart_update(element, valueAccessor, fadama_categories);
    }
};

function category_barchart_init(element, valueAccessor, mode, categories) {
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

	    var metrics = [];
	    $.each(categories, function(i, e) {
		    metrics.push(e.metric);
		});

            var bar_clicked = function() {
                var opt = element.wrapper.getChart().getSelection()[0].row;
                var metric = metrics[opt];
                window.location.href = '/dashboard/' + mode + '/reports/?metric=' + metric;
            };

            google.visualization.events.addListener(element.wrapper, 'select', bar_clicked);

            var active = ko.utils.unwrapObservable(valueAccessor());

            if(active) {
		var arr = [['Category', '']];
		$.each(categories, function(i, e) {
			arr.push([e.caption, active.data.by_category[e.field]]);
		    });

		var dataTable = google.visualization.arrayToDataTable(arr);
                element.wrapper.setDataTable(dataTable);
                element.wrapper.draw();
            }
        });
}

function category_barchart_update(element, valueAccessor, categories) {
    var active = ko.utils.unwrapObservable(valueAccessor());
    if (!element.wrapper || !active) {
	return;
    }

    var arr = [['Category', '']];
    $.each(categories, function(i, e) {
	    arr.push([e.caption, active.data.by_category[e.field]]);
	});

    var dataTable = google.visualization.arrayToDataTable(arr);
    element.wrapper.setDataTable(dataTable);
    element.wrapper.draw();
}

function current_chart_update(element, valueAccessor, viewModel, funcs, onclick) {
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
    
    var data = [['Category', '']];
    var raw_data = monthly_datapoints(active, metric);
    
    $.each(funcs.get_ordering(metric), function(i, e) {
            data.push([funcs.get_caption(metric, e), raw_data[e] || 0]);
        });
    
    var chart_type = 'PieChart';
    
    var chart = new google.visualization[chart_type](element);
    chart.draw(google.visualization.arrayToDataTable(data), options);
    
    if (onclick) {
	google.visualization.events.addListener(chart, 'select', function() { onclick(chart); });
    }
}

ko.bindingHandlers.pbf_current_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	current_chart_update(element, valueAccessor, viewModel, {get_ordering: get_pbf_ordering, get_caption: get_pbf_caption});
    }
};

function historical_chart_init(element, valueAccessor) {
    google.setOnLoadCallback(function() {
            valueAccessor(valueAccessor());
            element.charts_init = true;
        });
}

function historical_chart_update(element, valueAccessor, viewModel, funcs, onclick) {
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
    
    var labels = ['Month'];
    var raw_data = monthly_datapoints(active, metric);
    $.each(funcs.get_ordering(metric), function(i, e) {
            labels.push(funcs.get_caption(metric, e));
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
	    $.each(funcs.get_ordering(metric), function(i, e) {
                    row.push(raw_data[e] || 0);
                });
	}
	data.push(row);
    }
    
    var chart = new google.visualization.ColumnChart(element);
    chart.draw(google.visualization.arrayToDataTable(data), options);

    if (onclick) {
	google.visualization.events.addListener(chart, 'select', function() { onclick(chart); });
    }
}

ko.bindingHandlers.pbf_historical_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	historical_chart_init(element, valueAccessor);
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	historical_chart_update(element, valueAccessor, viewModel, {get_ordering: get_pbf_ordering, get_caption: get_pbf_caption});
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
	current_chart_update(element, valueAccessor, viewModel,
            {get_ordering: get_fadama_ordering, get_caption: get_fadama_subcategory_caption},
	    function(chart) {
		if (chart.getSelection().length === 0) {
		    return;
		}

		var opt = chart.getSelection()[0].row;
		var subcat = viewModel.subcategories()[opt + 1]; // the first is 'all', so offset by 1
		viewModel.active_subcategory(subcat);
	    });
    }
};

ko.bindingHandlers.fadama_historical_chart = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	historical_chart_init(element, valueAccessor);
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
	historical_chart_update(element, valueAccessor, viewModel, {get_ordering: get_fadama_ordering, get_caption: get_fadama_subcategory_caption}, function(chart) {
		if (chart.getSelection().length === 0) {
		    return;
		}

		var opt = chart.getSelection()[0].column;
		var subcat = viewModel.subcategories()[opt]; // the first is 'all', so don't offset by 1
		viewModel.active_subcategory(subcat);
	    });
    }
};
