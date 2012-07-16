// Misc. functions

function get_fadama_caption(metric, value) {
    return {
        satisf: {
            True: 'Satisfied',
            False: 'Unsatisfied'
        },
        serviceprovider: {
            notfind: 'Not Finding',
            notstarted: 'Not Started',
            delay: 'Delays',
            stopped: 'Abandoned Project',
            substandard: 'Substandard Service',
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
            bank: 'Bank Account Opening',
            delay: 'Delayed Funding',
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
    var key = {
        satisf: 'satisfied'
    }[metric] || metric;
    return month.stats[key];
}