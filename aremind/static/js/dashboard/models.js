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
    this.__all_clinics = new FadamaFacilityModel({id: -1, name: 'All Sites'});

    this.active_facility = ko.observable();
    this.active_metric = ko.observable(DEFAULT_METRIC || null);
    this.active_month = ko.observable();

    this.active_fug = ko.observable();
    this.active_subcategory = ko.observable();

    var model = this;

    this.load = function(data) {
        if (this.facilities().length === 0) {
            var facs = $.map(data.facilities, function(f) {
                return new FadamaFacilityModel(f);
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
            return new FadamaMonthlyDetailModel(m, model);
        }));
        this.active_month(this.monthly.slice(active_month_ix)[0]);
    };

    this.subcategories = ko.computed(function() {
        var __all = {val: 'all', text: 'All Sub-categories'};

        if (!model.active_metric() || model.active_metric() == 'all' || model.active_metric() == 'satisf') {
            return [__all];
        }

        var opts = $.map(get_ordering(model.active_metric()), function(e) {
            return {val: e, text: get_caption(model.active_metric(), e)};
        });
        opts.splice(0, 0, __all);
        return opts;
    });

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

        if(id === null) {
            return f;
        }

        $.each(this.facilities(), function(i, e) {
            if(e.id() == id) {
                f = e;
                return false;
            }
        });
        return f;
    };

    this.collapse_logs = function(active) {
        $.each(this.monthly(), function(i, e) {
            $.each(e.logs(), function(i, e) {
                if (e != active) {
                    e.expanded(false);
                }
            });
        });
    };
}

function FadamaFacilityModel(data) {
    this.id = ko.observable(data.id);
    this.name = ko.observable(data.name);

    if (data.id == -1) {
        data.fugs = [];
    }
    
    this.__all_fugs = 'All FUGs';
    data.fugs.splice(0, 0, this.__all_fugs);
    this.fugs = ko.observable(data.fugs);
}

function FadamaMonthlyDetailModel(data, root) {
    this.logs = ko.observableArray($.map(data.logs, function(l) {
        return new FadamaLogModel(l, root);
    }));
    this.month_label = ko.observable(data.month);
    this.stats = data.stats;
    this.clinic_totals = data.clinic_totals;

    this.any_logs_relevant = function(root) {
        var relev = false;
        $.each(this.logs(), function(i, e) {
            if (e.is_relevant(root)) {
                relev = true;
                return false;
            }
        });
        
        return relev;
    };
}

function FadamaLogModel(data, root) {
    this.id = ko.observable(data.id);
    this.site = ko.observable(data.site_name);
    this.fug = ko.observable(data.fug);
    this.date = ko.observable(data.display_time);
    this.satisfied = ko.observable(data.satisfied);
    this.proxy = ko.observable(data.proxy);
    this.thread = ko.observableArray($.map(data.thread, function(c) {
        return new CommModel(c);
    }));

    this.expanded = ko.observable(false);
    this.toggle = function() {
        this.expanded(!this.expanded());
        root.collapse_logs(this);
    };

    var categories = ['serviceprovider', 'people', 'land', 'info', 'ldp', 'financial'];
    var category = null;
    $.each(categories, function(i, e) {
        if (data[e] != null) {
            category = e;
            return false;
        }
    });
  
    this.category = ko.observable(category);
    this.subcategory = ko.observable(data[category]);
    this.message = ko.observable(data.message);

    var model = this;
    this.inquiry = ko.observable();
    this._inquiry = ko.computed({
        read: function () {
            return (model.proxy() ? 'it is not possible to message the beneficiary because they reported through a proxy' : model.inquiry());
        },
        write: function (value) {
            if (!model.proxy()) {
              model.inquiry(value);
            }
        },
        owner: this
    });
    this.note = ko.observable();

    this.send_message = function() {
        this.new_thread_msg('inquiry', this.inquiry());
    };

    this.new_note = function() {
        this.new_thread_msg('note', this.note());
    };

    this.new_thread_msg = function(type, content) {
        var model = this;
        $.post('/dashboard/fadama/message/', {id: this.id(), type: type, text: content, user: 'demo user'}, function(data) {
        model.thread.push(new CommModel(data));
        model[type == 'inquiry' ? 'inquiry' : 'note'](null);
            if (type == 'inquiry') {
            alert('Your message has been sent to the beneficiary (to the phone number they used to provide their feedback). You will be notified when they respond.');
            }
        });
    };
    
    this.category_caption = ko.computed(function() {
        return {
            'serviceprovider': 'Service Providers',
            'people': 'Stakeholders',
            'land': 'Land Issues',
            'info': 'Lack of Information',
            'ldp': 'LDP Approval',
            'financial': 'Financial Issues'
        }[model.category()];
    });
    this.subcategory_caption = ko.computed(function() {
        return get_fadama_caption(model.category(), model.subcategory());
    });

    this.is_relevant = function(root) {
        return (this.category() == root.active_metric() || root.active_metric() == 'all' || root.active_metric() == 'satisf') &&
           (this.fug() == root.active_fug() || root.active_fug() == 'All FUGs') &&
           (this.subcategory() == root.active_subcategory().val || root.active_subcategory().val == 'all');
    };
    
    this._autocollapse = ko.computed(function() {
        if (!model.is_relevant(root)) {
            model.expanded(false);
        }
    });
}

function CommModel(data) {
    this.author = ko.observable(data.author);
    this.type = ko.observable(data.type);
    this.date = ko.observable(data.date_fmt);
    this.text = ko.observable(data.text);

    var model = this;
    this.display = ko.computed(function() {
        if (model.type() == 'note') {
            return ['note', 'left by', model.author()];
        } else if (model.type() == 'inquiry') {
            return ['message to beneficiary', 'sent by', model.author()];
        } else if (model.type() == 'response') {
            return ['response', 'from', 'beneficiary'];
        }
    });
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
