var DEFAULT_SITE = urlParam('site');
var DEFAULT_METRIC = urlParam('metric');

function urlParam(name) {
    var param = decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[null])[1]
    );

    if(param === "undefined") {
        return null;
    }

    return param;
}

function get_caption(metric, value) {
    return {
        satisf: {
            True: 'Satisfied',
            False: 'Unsatisfied'
        },
        serviceprovider: {
            notfind: 'Not Finding',
            delay: 'Delays',
            stopped: 'Stopped Project',
            other: 'Other'
        },
        people: {
            state: 'State Officials',
            fug: 'FUG',
            fca: 'FCA',
            facilitator: 'Facilitators',
            other: 'Other'
        },
        land: {
            True: 'Yes',
            False: 'No'
        },
        info: {
            market: 'Market',
            input: 'Input',
            other: 'Other'
        },
        ldp: {
            delay: 'Delays',
            other: 'Other'
        },
        financial: {
            bank: 'Bank Account Opening',
            delay: 'Delayed Funding',
            other: 'Other'
        }
    }[metric][value];
}

function get_ordering(metric) {
    return {
        satisf: ['True', 'False'],
        serviceprovider: ['notfind', 'delay', 'stopped', 'other'],
        people: ['state', 'fug', 'fca', 'facilitator', 'other'],
        land: ['True', 'False'],
        info: ['market', 'input', 'other'],
        ldp: ['delay', 'other'],
        financial: ['bank', 'delay', 'other']
    }[metric];
}

function monthly_datapoints(month, metric) {
    var key = {
        satisf: 'satisfied'
    }[metric] || metric;
    return month.stats[key];
}

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

function PBFDetailViewModel() {
    this.monthly = ko.observableArray();
    this.facilities = ko.observableArray();
    this.__all_clinics = new FacilityModel({id: -1, name: 'All Clinics'});

    this.active_facility = ko.observable();
    this.active_metric = ko.observable(DEFAULT_METRIC || null);
    this.active_month = ko.observable();

    this.load = function(data) {
        if (this.facilities().length === 0) {
            var facs = $.map(data.facilities, function(f) {
                return new FacilityModel(f);
            });
            
            facs.splice(0, 0, this.__all_clinics);
            this.facilities(facs);

            var default_facility = this.facility_by_id(DEFAULT_SITE);
            if (default_facility) {
                this.active_metric('satisf');
                this.active_facility(default_facility);
            }
        }

        var active_month_ix = (this.active_month() ? this.monthly.indexOf(this.active_month()) : -1);
        this.monthly($.map(data.monthly, function(m) {
            return new MonthlyDetailModel(m);
        }));
        this.active_month(this.monthly.slice(active_month_ix)[0]);
    };

    this.ajax_load = function(facility_id) {
        var params = facility_id != null ? {site: facility_id} : {};
        var model = this;
        $.get('/dashboard/pbf/api/detail', params, function(data) {
            // console.log(params, data);
            model.load(data);
        }, 'json');
    };

    this.prevmonth = function() {
        this.month_incr(-1);
    };

    this.nextmonth = function() {
        this.month_incr(1);
    };

    this.month_incr = function(k) {
        var i = this.monthly.indexOf(this.active_month());
        i += k;
        if (i >= this.monthly().length) {
            i = this.monthly().length - 1;
        } else if (i <= 0) {
            i = 0;
        }
        this.active_month(this.monthly()[i]);
    };

    this.is_metric_active = function(code) {
        return (this.active_metric() == 'all' || this.active_metric() == code);
    };

    var model = this;
    this._facility_reload = ko.computed(function() {
        var fac = model.active_facility();
        model.ajax_load(fac != null && fac.id() != -1 ? fac.id() : null);
    });

    this.facility_by_id = function(id) {
        var f = null;

        if(id === null) {
            return f;
        }

        $.each(this.facilities(), function(i, e) {
            if (id != null && e.id() == id) {
                f = e;
                return false;
            }
        });
        return f;
    };

    this.displayMap = function() {
        if(this.active_metric() == 'all') {
            // Fire the event so that the map resizes after
            // showing the div
            $('.map').trigger('showmap');
            return true;
        }

        return false;
    };
}

function FadamaDetailViewModel() {
    this.monthly = ko.observableArray();
    this.facilities = ko.observableArray();
    this.__all_clinics = new FacilityModel({id: -1, name: 'All Sites'});

    this.active_facility = ko.observable();
    this.active_metric = ko.observable(DEFAULT_METRIC || null);
    this.active_month = ko.observable();

    this.load = function(data) {
        if (this.facilities().length === 0) {
            var facs = $.map(data.facilities, function(f) {
                return new FacilityModel(f);
            });
            facs.splice(0, 0, this.__all_clinics);
            this.facilities(facs);

            var default_facility = this.facility_by_id(DEFAULT_SITE);
            if (default_facility) {
                this.active_metric('satisf');
                this.active_facility(default_facility);
            }
        }

        var active_month_ix = (this.active_month() ? this.monthly.indexOf(this.active_month()) : -1);
        this.monthly($.map(data.monthly, function(m) {
            return new MonthlyDetailModel(m);
        }));
        this.active_month(this.monthly.slice(active_month_ix)[0]);
    };

    this.ajax_load = function(facility_id) {
        var params = facility_id != null ? {site: facility_id} : {};
        var model = this;
        $.get('/dashboard/fadama/api/detail', params, function(data) {
                console.log(params, data);
                model.load(data);
            }, 'json');
    };

    this.prevmonth = function() {
        this.month_incr(-1);
    };

    this.nextmonth = function() {
        this.month_incr(1);
    };

    this.month_incr = function(k) {
        var i = this.monthly.indexOf(this.active_month());
        i += k;
        if (i >= this.monthly().length) {
            i = this.monthly().length - 1;
        } else if (i <= 0) {
            i = 0;
        }
        this.active_month(this.monthly()[i]);
    };

    this.is_metric_active = function(code) {
        return (this.active_metric() == 'all' || this.active_metric() == code);
    };

    var model = this;
    this._facility_reload = ko.computed(function() {
        var fac = model.active_facility();
        model.ajax_load(fac != null && fac.id() != -1 ? fac.id() : null);
    });

    this.facility_by_id = function(id) {
        var f = null;
        $.each(this.facilities(), function(i, e) {
            if (id != null && e.id() == id) {
                f = e;
                return false;
            }
        });
        return f;
    };
}


function FacilityModel(data) {
    this.id = ko.observable(data.id);
    this.name = ko.observable(data.name);
}

function MonthlyDetailModel(data) {
    this.logs = ko.observableArray($.map(data.logs, function(l) {
        return new LogModel(l);
    }));
    this.month_label = ko.observable(data.month);
    this.stats = data.stats;
    this.clinic_totals = data.clinic_totals;
}

function LogModel(data) {
    this.id = ko.observable(data.id);
    this.site = ko.observable(data.site_name);
    this.date = ko.observable(data.display_time);
    this.satisfied = ko.observable(data.satisfied);
    this.wait_bucket = ko.observable(data.wait_bucket);
    this.cleanliness = ko.observable(data.cleanliness);
    this.friendliness = ko.observable(data.staff_friendliness);
    this.drugs_avail = ko.observable(data.drug_availability);
    this.price_display = ko.observable(data.price_display);
    this.message = ko.observable(data.message);

    this.disp_wait = ko.computed(function() {
        return {
            '<2': '< 2 hrs',
            '2-4': '2\u20134 hrs',
            '>4': '> 4 hrs'
        }[this.wait_bucket()];
    }, this);
}
