function showLoadingModal() {
    $('.modal-backdrop').css('display', '');
    $('#loading-modal').show();
}

function hideLoadingModal() {
    // Wait an extra half-second to give some time for data to be rendered.
    setTimeout(function() {
        $('#loading-modal').hide();
        $('.modal-backdrop').css('display', 'none');
    }, 500);
}

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
    {metric: 'pricedisp', field: 'price_display', caption: 'Prices Displayed'},
    {metric: 'drugavail', field: 'drug_availability', caption: 'Drug Availability'},
    {metric: 'clean', field: 'cleanliness', caption: 'Cleanliness & Hygiene'},
];

fadama_categories = [
    {metric: 'serviceprovider', field: 'serviceprovider', caption: 'Service Providers'},
    {metric: 'people', field: 'people', caption: 'Stakeholders'},
    {metric: 'land', field: 'land', caption: 'Land Issues'},
    {metric: 'info', field: 'info', caption: 'Lack of Information'},
    {metric: 'ldp', field: 'ldp', caption: 'LDP Approval'},
    {metric: 'financial', field: 'financial', caption: 'Financial Issues'},
];

function get_fadama_caption(metric, value) {
    return {
        satisf: {
            True: 'Satisfied',
            False: 'Unsatisfied'
        },
        serviceprovider: {
            notfind: "Can't Find",
            notstarted: 'Not Started',
            delay: 'Delays',
            stopped: 'Abandoned project',
            substandard: 'Substandard service',
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
            notfind: 'Not Finding',
            suitability: 'Not Suitable',
            ownership: 'Ownership',
            other: 'Other'
        },
        info: {
            market: 'Market',
            input: 'Input',
            credit: 'Access to Credit',
            other: 'Other'
        },
        ldp: {
            delay: 'Delays',
            other: 'Other'
        },
        financial: {
            bank: 'Bank account opening',
            delay: 'Delayed funding',
            other: 'Other'
        }
    }[metric][value];
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
            False: 'Not clean'
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
            False: 'Not displayed'
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

function get_pbf_metric_model_field(metric) {
    return {
	satisf: 'satisfied',
	wait: 'wait_bucket',
	clean: 'cleanliness',
	friendly: 'friendliness',
	drugavail: 'drugs_avail',
	pricedisp: 'price_display',
    }[metric];
}

function get_pbf_metric_ajax_field(metric) {
    return {
	satisf: 'satisfied',
	wait: 'wait_bucket',
	clean: 'cleanliness',
	friendly: 'staff_friendliness',
	drugavail: 'drug_availability',
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
    var key = get_pbf_metric_ajax_field(metric) || metric;
    return month.stats[key];
}

function dashboard_ajax(model, url, params) {
    $.ajax({
        url: url,
        data: params,
        dataType: "json",
        beforeSend: showLoadingModal,
        success: function(data) {
            console.log(url, params || '-', data);            
            model.load(data)
        },
        complete: hideLoadingModal
    });
}
