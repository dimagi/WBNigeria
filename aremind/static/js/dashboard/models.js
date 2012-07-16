function MonthlyStatsModel(data) {
    this.total = ko.observable(data.total);
    this.month_label = ko.observable(data.month);

    this.data = data;
}

function DashboardViewModel() {
    this.stats = ko.observableArray();
    this.active_month = ko.observable();

    this.load = function(data) {
        this.stats($.map(data.stats, function(st) {
            return new MonthlyStatsModel(st);
        }));
        this.active_month(this.stats.slice(-1)[0]);
    };

    this.prevmonth = function() {
        this.month_incr(-1);
    };

    this.nextmonth = function() {
        this.month_incr(1);
    };
 
    this.month_incr = function(k) {
        var i = this.stats.indexOf(this.active_month());
        i += k;
        if (i >= this.stats().length) {
            i = this.stats().length - 1;
        } else if (i <= 0) {
            i = 0;
        }
        this.active_month(this.stats()[i]);
    };
}
