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
    this.__all_clinics = new PbfFacilityModel({id: -1, name: 'All Clinics'});
    this.__other_clinics = new PbfFacilityModel({id: 999, name: 'Other'});

    this.active_facility = ko.observable();
    this.active_metric = ko.observable(DEFAULT_METRIC || null);
    this.active_month = ko.observable();

    this.taggable_contacts = ko.observableArray();

    var model = this;

    this.load = function(data) {
        if (this.facilities().length === 0) {
            var facs = $.map(data.facilities, function(f) {
                return new PbfFacilityModel(f);
            });

            facs.splice(0, 0, this.__all_clinics);
            facs.push(this.__other_clinics);
            this.facilities(facs);

            var default_facility = this.facility_by_id(DEFAULT_SITE);
            if (default_facility) {
                this.active_metric('satisf');
                this.active_facility(default_facility);
            }
        }

        var active_month_key = (this.active_month() ? this.active_month()._month : null);
        this.monthly($.map(data.monthly, function(m) {
            return new PbfMonthlyDetailModel(m, model);
        }));
        this.month_set(active_month_key);
    };

    this.ajax_load = function(facility_id) {
        var params = facility_id != null ? {site: facility_id} : {};
        var model = this;
        dashboard_ajax(model, '/dashboard/pbf/api/detail', params);
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

    this.month_set = function(key) {
        var match = null;
        $.each(this.monthly(), function(i, e) {
                if (e._month >= key) {
                    match = e;
                    return false;
                }
            });
        if (match == null && this.monthly().length > 0) {
            match = this.monthly.slice(-1)[0];
        }
        this.active_month(match);
    }

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

    this.collapse_logs = function(active) {
        $.each(this.monthly(), function(i, e) {
            $.each(e.logs(), function(i, e) {
                if (e != active) {
                    e.expanded(false);
                }
            });
        });
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

function PbfFacilityModel(data) {
    this.id = ko.observable(data.id);
    this.name = ko.observable(data.name);
}

function PbfMonthlyDetailModel(data, root) {
    this.logs = ko.observableArray($.map(data.logs, function(l) {
        return new PbfLogModel(l, root);
    }));
    this.month_label = ko.observable(data.month);
    this.total = ko.observable(data.total);
    this.stats = data.stats;
    this.clinic_totals = data.clinic_totals;

    this.disp_logs = ko.computed(function() {
            var filtered = [];
            var metric = root.active_metric();
            $.each(this.logs(), function(i, e) {
                    if (metric == 'all' || e[get_pbf_metric_model_field(metric)]() != null) {
                        filtered.push(e);
                    }
                });
            return filtered;
        }, this);
}

function PbfLogModel(data, root) {
    var model = this;

    this.id = ko.observable(data.id);
    this.site = ko.observable(data.site_name);
    this.for_this_site = ko.observable(data.for_this_site);
    this.date = ko.observable(data.display_time);
    this.satisfied = ko.observable(data.satisfied);
    this.wait_bucket = ko.observable(data.wait_bucket);
    this.cleanliness = ko.observable(data.cleanliness);
    this.friendliness = ko.observable(data.staff_friendliness);
    this.drugs_avail = ko.observable(data.drug_availability);
    this.price_display = ko.observable(data.price_display);
    this.message = ko.observable(data.message);
    
    this.thread = ko.observableArray($.map(data.thread || [], function(c) { // FIXME
        return new CommModel(c, model);
    }));
    this.tagged_contacts = ko.observableArray();

    this.root = root;
    
    this.disp_wait = ko.computed(function() {
            return {
                '<2': '< 2 hrs',
                '2-4': '2\u20134 hrs',
                '>4': '> 4 hrs',
            }[this.wait_bucket()];
        }, this);

    this.expanded = ko.observable(false);
    this.toggle = function() {
        this.expanded(!this.expanded());
        root.collapse_logs(this);
    };

    this.note = ko.observable();

    this.submission_in_progress = false;

    this.new_note = function() {
        if (this.submission_in_progress) return;
        new_thread_msg('pbf', this, 'note', this.note());

        // reset tagged users
        this.tagged_contacts([]);
        $('select.tags option:selected').removeAttr("selected");
    };

}

function new_thread_msg(program, log, type, content) {
    // Don't submit empty comments
    if (!content) return;
    var form = $('#message-form-' + log.id());
    var url = form.attr('action');
    $(':input', form).prop('disabled', true);
    $('.btn.submit', form).addClass('disabled');
    // Prevent duplicate/parallel submission
    log.submission_in_progress = true;

    var params = {
        comment_type: type,
        text: content,
        contact_tags: (type == 'note' ? log.tagged_contacts() : []),
        author: 'demo user'
    };
    params[program + '_report'] = log.id();

    $.ajax({
        type: 'POST',
        url: url,
        dataType: 'json',
        traditional: true,
        data: params,
        success: function(data) {
            // Add submission to the UI
            log.thread.push(new CommModel(data, log));
            log[type == 'inquiry' ? 'inquiry' : 'note'](null);
            if (type == 'inquiry') {
                alert('Your message has been sent to the beneficiary (to the phone number they used to provide their feedback). You will be notified when they respond.');
            }
        }
    }).error(function() {
        alert('There was an error adding your message.');
    }).complete(function() {
        // Submission finished. Restore the form controls
        log.submission_in_progress = false;
        $(':input', form).prop('disabled', false);
        $('.btn.submit', form).removeClass('disabled');
    });
}

function FadamaDetailViewModel() {
    this.monthly = ko.observableArray();
    this.taggable_contacts = ko.observableArray();
    this.facilities = ko.observableArray();
    this.__all_clinics = new FadamaFacilityModel({id: -1, name: 'All Sites'});
    this.__other_clinics = new PbfFacilityModel({id: -999, name: 'Other'});

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
            facs.push(this.__other_clinics);
            this.facilities(facs);

            var default_facility = this.facility_by_id(DEFAULT_SITE);
            if (default_facility) {
                this.active_metric('satisf');
                this.active_facility(default_facility);
            }
        }

	this.taggable_contacts($.map(data.taggable_contacts, function(e) {
		    return new TaggablesByState(e);
		}));

        var active_month_key = (this.active_month() ? this.active_month()._month : null);
        this.monthly($.map(data.monthly, function(m) {
            return new FadamaMonthlyDetailModel(m, model);
        }));
        this.month_set(active_month_key);
    };

    this.subcategories = ko.computed(function() {
        var __all = {val: 'all', text: 'All Sub-categories'};

        if (!model.active_metric() || model.active_metric() == 'all' || model.active_metric() == 'satisf') {
            return [__all];
        }

        var opts = $.map(get_fadama_ordering(model.active_metric()), function(e) {
            return {val: e, text: get_fadama_caption(model.active_metric(), e)};
        });
        opts.splice(0, 0, __all);
        return opts;
    });

    this.ajax_load = function(facility_id) {
        var params = facility_id != null ? {site: facility_id} : {};
        var model = this;
        dashboard_ajax(model, '/dashboard/fadama/api/detail', params);
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

    this.month_set = function(key) {
        var match = null;
        $.each(this.monthly(), function(i, e) {
                if (e._month >= key) {
                    match = e;
                    return false;
                }
            });
        if (match == null && this.monthly().length > 0) {
            match = this.monthly.slice(-1)[0];
        }
        this.active_month(match);
    }

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

function FadamaLogsForContactModel(data, taggables) {
    this.active_metric = ko.observable('all');
    this.active_fug = ko.observable('All FUGs');
    this.active_subcategory = ko.observable({val: 'all'});
    this.taggable_contacts = ko.observableArray();

    this.taggable_contacts($.map(taggables, function(e) {
		return new TaggablesByState(e);
	    }));

    $.each(data, function(i, e) {
        e.from_same = [];
    });

    this.active_month = ko.observable(new FadamaMonthlyDetailModel({logs: data, stats: {}}, this));

    this.collapse_logs = function(active) {
        $.each(this.active_month().logs(), function(i, e) {
            if (e != active) {
                e.expanded(false);
            }
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

    this.count_for_category = ko.computed(function() {
            var data = monthly_datapoints(this, root.active_metric());
            var count = 0;
            $.each(data || {}, function(k, v) {
                    count += v;
                });
            return count;
        }, this);
}

function FadamaLogModel(data, root) {
    var model = this;

    this.id = ko.observable(data.id);
    this.site = ko.observable(data.site_name);
    this.fug = ko.observable(data.fug);
    this.for_this_site = ko.observable(data.for_this_site);
    this.date = ko.observable(data.display_time);
    this.satisfied = ko.observable(data.satisfied);
    this.can_contact = ko.observable(data.can_contact);
    this.proxy = ko.observable(data.proxy);
    this.thread = ko.observableArray($.map(data.thread, function(c) {
        return new CommModel(c, model);
    }));
    this.contact = ko.observable(data.contact);
    this.other_recent = ko.observable(data.from_same.length);
    this.tagged_contacts = ko.observableArray();

    this.root = root;

    this.expanded = ko.observable(false);
    this.toggle = function() {
        this.expanded(!this.expanded());
        root.collapse_logs(this);
    };

    var categories = ['serviceprovider', 'people', 'land', 'info', 'ldp', 'financial', 'misc'];
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

    this.contactable = ko.computed(function() {
	    return !this.proxy() && this.can_contact();
	}, this);
    this.no_contact_message = ko.computed(function() {
	    if (this.proxy()) {
		return 'it is not possible to message the beneficiary because they reported through a proxy';
	    } else if (!this.can_contact()) {
		return 'the beneficiary does not wish to be contacted further';
	    } else {
		return null;
	    }
	}, this);

    var model = this;
    this.inquiry = ko.observable();
    this._inquiry = ko.computed({
        read: function () {
            return model.no_contact_message() || model.inquiry();
        },
        write: function (value) {
            if (model.contactable()) {
              model.inquiry(value);
            }
        },
        owner: this
    });
    this.note = ko.observable();

    this.submission_in_progress = false;

    this.send_message = function() {
        if (this.submission_in_progress) return;
        new_thread_msg('fadama', this, 'inquiry', this.inquiry());
    };

    this.new_note = function() {
        if (this.submission_in_progress) return;
        new_thread_msg('fadama', this, 'note', this.note());

        // reset tagged users
        this.tagged_contacts([]);
        $('select.tags option:selected').removeAttr("selected");
    };
    
    this.category_caption = ko.computed(function() {
        return {
            'serviceprovider': 'Service Providers',
            'people': 'Stakeholders',
            'land': 'Land Issues',
            'info': 'Lack of Information',
            'ldp': 'LDP Approval',
            'financial': 'Financial Issues',
            'misc': 'Misc. Feedback'
        }[model.category()];
    });
    this.subcategory_caption = ko.computed(function() {
        return get_fadama_caption(model.category(), model.subcategory());
    });

    this.is_relevant = function(root) {
        return (this.category() == root.active_metric() || root.active_metric() == 'all' ||
                (root.active_metric() == 'satisf' && this.satisfied() != null)) &&
           (this.fug() == root.active_fug() || root.active_fug() == 'All FUGs') &&
           (this.subcategory() == root.active_subcategory().val || root.active_subcategory().val == 'all');
    };

    this._autocollapse = ko.computed(function() {
        if (!model.is_relevant(root)) {
            model.expanded(false);
        }
    });

    this.append_text = ko.computed(function() {
        return '';
    });

    this.prepend_text = FC_PREFIX;

    var TOTAL_CHARS = 160;
    this.max_characters = ko.computed(function() {
        return TOTAL_CHARS - model.append_text().length - (model.prepend_text + ' ').length;
    });

    this.chars_remaining = ko.computed(function() {
        return this.max_characters() - (this.inquiry() || '').length;
    }, this);
}

function CommModel(data, thread) {
    this.id = data.id;
    this.author = ko.observable(data.author);
    this.type = ko.observable(data.type);
    this.date = ko.observable(data.date_fmt);
    this.text = ko.observable(data.text);
    this.extra = ko.observable(data.extra || {});
    this.tags = ko.observableArray(data.contact_tags);

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

    this.delete_note = function() {
        if (!confirm('Are you sure you want to delete this note?')) {
            return;
        }

        var model = this;
        $.post(NOTE_DELETE_URL, {id: this.id}, function(data) {
            var ix = -1;
            $.each(thread.thread(), function(i, e) {
                if (e == model) {
                    ix = i;
                    return false;
                }
            });
            if (ix != -1) {
                thread.thread.splice(ix, 1);
            }
        });
    }
}

function TaggablesByState(data) {
    this.state = ko.observable(data.state);
    this.users = ko.observableArray($.map(data.users, function(e) {
		return new TaggableUserModel(e);
	    }));

    this.display_state = ko.computed(function() {
	    var st = this.state();
	    if (st == 'fct') {
		st = st.toUpperCase();
	    } else {
		st = st[0].toUpperCase() + st.substring(1);
	    }
	    return st + ' Officers';
	}, this);
}

function TaggableUserModel(u) {
    this.first_name = ko.observable(u.first_name);
    this.last_name = ko.observable(u.last_name);
    this.name = ko.computed(function() {
	    return this.last_name() + ', ' + this.first_name();
	}, this);
    this.id = ko.observable(u.user_id);
}
