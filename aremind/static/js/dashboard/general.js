// General shared functionality throughout the site
// Mostly for things contained in both PBF and Fadama dashboards

// Test data url
var data_url = '/dashboard/load/';

$(function() {
    // Make datepickers from any date inputs across the site
    $('form input.calendar').datepicker({
        'dateFormat': 'M yy'
    });

    // Create a modal dialog if any divs are found
    $('div.contact-modal').dialog({
        'autoOpen': false,
        'resizable': false,
        'modal': true,
        'minHeight': 400,
        'minWidth': $('div.contact-modal').width()
    });

    /*
    //DataTable-ify all tables
    var table = $('table#reports-table').dataTable({
        'sDom': '<t>'
    });

    // Add a row of content for the report info when clicked
    $('#reports-table a[data-target]').click(function(e) {
        var report = $(this).data('target'),
            content = $('.report-info[data-report=' + report + ']').html(),
            row = $(this).parents('tr')[0];

        if(table.fnIsOpen(row)) {
            table.fnClose(row);
        } else {
            table.fnOpen(row, content, 'class');
        }
    });

    // Attach search fields to tables
    $('#search').keyup(function(e) {
        table.fnFilter($(this).val());
    });
    */

    // Enable the marks on tables
    ko.bindingHandlers.yn = {
        update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
            var val = ko.utils.unwrapObservable(valueAccessor());

	    $(element).text(val ? 'Yes' : 'No');
	    /*
            $(element).empty();
            if (val != null) {
                var $img = $('<img />');
                $img.attr('src', '/static/images/icon_' + (val ? 'success' : 'error') + '.gif');
                $img.attr('alt', val ? 'Yes' : 'No');
                $(element).append($img);
            }
	    */
        }
    };

    ko.bindingHandlers.fadama_category_color = {
        update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
            var coltype = ko.utils.unwrapObservable(valueAccessor());
	    var root = viewModel.root;

	    if (root.active_metric() == 'all') {
		var color = '';
	    } else if (root.active_metric() == 'satisf') {
		var _color = get_subcategory_color('satisf', viewModel.satisfied(), get_fadama_ordering);
		var color = (coltype == 'satisf' ? _color : '');
	    } else {
		var _color = get_subcategory_color(viewModel.category(), viewModel.subcategory(), get_fadama_ordering);
		var color = (coltype == 'subcat' ? _color : '');
	    }

	    $(element).css('background-color', color);
        }
    };

    ko.bindingHandlers.pbf_category_color = {
        update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
            var coltype = ko.utils.unwrapObservable(valueAccessor());
	    var root = viewModel.root;

	    if (root.active_metric() == 'all') {
		var color = '';
	    } else {
		var field = get_pbf_metric_field(coltype);
		var color = get_subcategory_color(coltype, viewModel[field](), get_pbf_ordering);
	    }

	    $(element).css('background-color', color);
        }
    };

    // Enable all alerts
    $('.alert').alert().bind('close', function(e) {
        // Handle the dismissing here
        // Some sort of server-side processing/error checking/etc.
    });
});