// General shared functionality throughout the site

$(function() {
    // Make datepickers from any date inputs across the site
    $('form input.calendar').datepicker({
        'dateFormat': 'M yy'
    });
});