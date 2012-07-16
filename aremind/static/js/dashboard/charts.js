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
                    textPosition: 'in'
                },
                chartArea: {
                    top: 0,
                    left: 0,
                    width: '100%'
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
        google.load('visualization', '1', { packages: ['corechart'] });
        google.setOnLoadCallback(function() {
            var options = {
                vAxis: {
                    textPosition: 'in'
                },
                chartArea: {
                    top: 0,
                    left: 0,
                    width: '100%'
             }
            };

            element.wrapper = new google.visualization.ChartWrapper({
                chartType: 'BarChart',
                options: options,
                containerId: $(element).attr('id')
            });

            var bar_clicked = function() {
                var opt = element.wrapper.getChart().getSelection()[0].row;
                var metric = ['serviceprovider', 'people', 'land', 'info', 'ldp', 'financial'];
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
