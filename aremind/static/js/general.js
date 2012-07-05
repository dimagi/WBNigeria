// General shared functionality throughout the site
// Mostly for things contained in both PBF and Fadama dashboards

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

    //DataTable-ify all tables
    var table = $('table#reports-table').dataTable({
        'sDom': '<t>'
    });

    // Attach search fields to tables
    $('#search').keyup(function(e) {
        table.fnFilter($(this).val());
    });

    // Enable all alerts
    $('.alert').alert().bind('close', function(e) {
        // Handle the dismissing here
        // Some sort of server-side processing/error checking/etc.
    });
});