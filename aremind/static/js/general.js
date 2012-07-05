// General shared functionality throughout the site

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

    $('#search').keyup(function(e) {
        table.fnFilter($(this).val());
    });
});