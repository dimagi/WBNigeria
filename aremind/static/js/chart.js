function getJsonData(url, options, cb) {
    $.getJSON(url, options, cb);
}

// Chart is a simple chart for a single months display
// Handles bar charts and pie charts
function Chart(container, dataTable, chartType, options) {
    this.container = container;
    this.dataTable = dataTable;
    this.chartType = chartType;
    this.options = options || {};
    this.wrapper = null;
}

// Callback for Google Charts
Chart.prototype.draw = function() {
    this.wrapper = this.wrapper || new google.visualization.ChartWrapper({
        chartType: this.chartType,
        dataTable: this.dataTable,
        options: this.options,
        containerId: this.container
    });
    this.wrapper.draw();
};

Chart.prototype.loadExperienceData = function(url, options) {
    var that = this;

    var updateChart = function(data, status, xhr) {
        var dataTable = google.visualization.arrayToDataTable([
            ['Category', ''],
            ['Satisfied', data['satisfied']],
            ['Unsatisfied', data['unsatisfied']]
        ]);
        that.wrapper.setDataTable(dataTable);
        that.wrapper.draw();
    };

    getJsonData(url, options, updateChart);
};

Chart.prototype.loadCategoryData = function(url, options) {
    var that = this;

    var updateChart = function(data, status, xhr) {
        var dataArray = [];
        
        // Process data here
        // A little more complicated than pie chart data
        // so leaving this until we have concrete data to work with

        var dataTable = google.visualization.arrayToDataTable(dataArray);
        that.wrapper.setDataTable(dataTable);
        that.wrapper.draw();
    };

    getJsonData(url, options, updateChart);
};

// A chart for multi month display column charts
function ColumnChart(container, dataTable, options) {
    this.container = container;
    this.dataTable = dataTable;
    this.options = options || {};
    this.wrapper = null;
}

// Callback for Google Charts
Chart.prototype.draw = function() {
    this.wrapper = this.wrapper || new google.visualization.ChartWrapper({
        chartType: 'ColumnChart',
        dataTable: this.dataTable,
        options: this.options,
        containerId: this.container
    });
    this.wrapper.draw();
};

Chart.prototype.loadData = function() {
    var that = this;

    var updateChart = function(data, status, xhr) {
        var dataArray = [];
        
        // Process data here
        // A little more complicated than pie chart/regular bar chart data
        // so leaving this until we have concrete data to work with

        var dataTable = google.visualization.arrayToDataTable(dataArray);
        that.wrapper.setDataTable(dataTable);
        that.wrapper.draw();
    };

    getJsonData(url, options, updateChart);
};
