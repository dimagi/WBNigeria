// Ajax without csrf exemption
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

// Misc. functions

pbf_categories = [
    {metric: 'wait', field: 'waiting_time', caption: 'Waiting Time'},
    {metric: 'friendly', field: 'staff_friendliness', caption: 'Staff Friendliness'},
    {metric: 'pricedisp', field: 'price_display', caption: 'Price Display'},
    {metric: 'drugavail', field: 'drug_availability', caption: 'Drug Availability'},
    {metric: 'clean', field: 'cleanliness', caption: 'Cleanliness & Hygiene'}
];

fadama_categories = [
    {metric: 'serviceprovider', field: 'serviceprovider', caption: 'Service Providers'},
    {metric: 'people', field: 'people', caption: 'People from Fadama'},
    {metric: 'land', field: 'land', caption: 'Land Issues'},
    {metric: 'info', field: 'info', caption: 'Information Issues'},
    {metric: 'ldp', field: 'ldp', caption: 'LDP Approval'},
    {metric: 'financial', field: 'financial', caption: 'Financial Issues'}
];

fadama_descriptions = {
    ldp: {
        name: 'LDP Approval',
        description: 'Delays with LDP approval or other LDP-related issues',
        subcategories: {
            delay: {
                name: 'Delays',
                description: 'Delays with LDP approval'
            },
            other: {
                name: 'Other',
                description: 'Other issues related to the LDP'
            }
        }
    },
    info: {
        name: 'Lack of Information',
        description: 'Lack of information on markets, agricultural inputs, credit options, or other issues',
        subcategories: {
            credit: {
                name: 'Access to credit',
                description: 'Lack of information on obtaining access to credit'
            },
            input: {
                name: 'Input',
                description: 'Lack of information on agricultural inputs: what to use or how to use them'
            },
            other: {
                name: 'Other',
                description: 'Other issues relating to lack of available information'
            },
            market: {
                name: 'Market',
                description: 'Lack of information on markets: access, pricing, or other issues'
            }
        }
    },
    serviceprovider: {
        name: 'Service Providers',
        description: 'Issues with finding a service provider, with the execution of the service provider contract, or with other related issues',
        subcategories: {
            notfind: {
                name: 'Not finding',
                description: 'Not able to find appropriate service providers'
            },
            delay: {
                name: 'Delays',
                description: 'Service provider was delayed in project execution'
            },
            substandard: {
                name: 'Substandard Service',
                description: 'Service provider delivered substandard service'
            },
            notstarted: {
                name: 'Not started',
                description: 'Service provider did not start project as agreed'
            },
            stopped: {
                name: 'Abandoned Project',
                description: 'Service provider abandoned project'
            },
            other: {
                name: 'Other',
                description: 'Other issues with service providers'
            }
        }
    },
    financial: {
        name: 'Financial Issues',
        description: 'Challenges in opening bank account, delays in receiving matching grant, or other financial issues',
        subcategories: {
            delay: {
                name: 'Delayed Funding',
                description: 'Delays in receiving matching grant'
            },
            bank: {
                name: 'Bank Account Opening',
                description: 'Issues with opening a bank account'
            },
            other: {
                name: 'Other',
                description: 'Other issues related to finances'
            }
        }
    },
    land: {
        name: 'Land Issues',
        description: 'Issues with finding land or finding suitable land, with land ownership, or other related issues',
        subcategories: {
            notfind: {
                name: 'Not finding',
                description: 'Not able to find land for project'
            },
            other: {
                name: 'Other',
                description: 'Other issues related to land'
            },
            ownership: {
                name: 'Ownership',
                description: 'Issue with land ownership'
            },
            suitability: {
                name: 'Not suitable',
                description: 'Not able to find land that is suitable for project'
            }
        }
    },
    people: {
        name: 'Stakeholders',
        description: 'Issues related to the different stakeholders: State PIU officials, FUG and FCA members, Facilitators, or others',
        subcategories: {
            fug: {
                name: 'FUG',
                description: 'Issue with FUG members'
            },
            other: {
                name: 'Other',
                description: 'Issue with other stakeholders'
            },
            facilitator: {
                name: 'Facilitators',
                description: 'Issue with Facilitators'
            },
            state: {
                name: 'State officials',
                description: 'Issue with State PIU officials'
            },
            fca: {
                name: 'FCA',
                description: 'Issue with FCA members'
            }
        }
    },
    satisf: {
        name: 'Satisfaction',
        description: 'Satisfaction',
        subcategories: {
            True: {
                name: 'Satisfied',
                description: 'Satisfied'
            },
            False: {
                name: 'Unsatisfied',
                description: 'Unsatisfied'
            }
        }
    }
};

function get_fadama_caption(metric, value) {
    return fadama_descriptions[metric]['subcategories'][value]['name'];
}

function get_fadama_ordering(metric) {
  return {
        satisf: ['True', 'False'],
        serviceprovider: ['notfind', 'notstarted', 'delay', 'stopped', 'substandard', 'other'],
        people: ['state', 'fug', 'fca', 'facilitator', 'other'],
        land: ['notfind', 'suitability', 'ownership', 'other'],
        info: ['market', 'input', 'credit', 'other'],
        ldp: ['delay', 'other'],
        financial: ['bank', 'delay', 'other']
    }[metric];
}

function get_pbf_caption(metric, value) {
    return {
        satisf: {
            True: 'Satisfied',
            False: 'Unsatisfied'
        },
        clean: {
            True: 'Clean',
            False: 'Dirty'
        },
        friendly: {
            True: 'Friendly',
            False: 'Not friendly'
        },
        drugavail: {
            True: 'Available',
            False: 'Unavailable'
        },
        pricedisp: {
            True: 'Displayed',
            False: 'Not on display'
        },
        wait: {
            '<2': '< 2 hrs',
            '2-4': '2\u20134 hrs',
            '>4': '> 4 hrs'
        }
    }[metric][value];
}

function get_pbf_ordering(metric) {
    var order = {
	wait: ['<2', '2-4', '>4'],
    }[metric];
    if (!order) {
	order = ['True', 'False'];
    }
    return order;
}

function get_pbf_metric_field(metric) {
    return {
	satisf: 'satisfied',
	wait: 'wait_bucket',
	clean: 'cleanliness',
	friendly: 'friendliness',
	drugavail: 'drugs_avail',
	pricedisp: 'price_display',
    }[metric];
}

function get_subcategory_color(cat, subcat, get_ordering) {
    var COLORS = [ // these must match the colors assigned by the charting api
		  '#aaf', //36c
		  '#faa', //e41
		  '#fca', //f90
		  '#aca', //192
		  '#cac', //090
		  '#ade', //09c
		   ];

    if (subcat === true) {
	subcat = 'True';
    } else if (subcat === false) {
	subcat = 'False';
    }

    var k = get_ordering(cat).indexOf(subcat);
    return COLORS[k];
}

function site_name(name, map) {
    if (name === null) {
        if (map.$sitename_ovl) {
            map.$sitename_ovl.remove();
            map.$sitename_ovl = null;
        }
    } else {
        if (!map.$sitename_ovl) {
            var $ovl = $('<div />');
            $ovl.css('z-index', 50000);
            $ovl.css('position', 'absolute');
            $ovl.css('bottom', 5);
            $ovl.css('left', 5);
            $ovl.addClass('sitename');
            $(map.getDiv()).append($ovl);
            map.$sitename_ovl = $ovl;
        }
        
        map.$sitename_ovl.text(name);
    }
}

function monthly_datapoints(month, metric) {
    var key = get_pbf_metric_field(metric) || metric;
    return month.stats[key];
}
