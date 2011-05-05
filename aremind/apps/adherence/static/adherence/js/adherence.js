$(document).ready(function() {
    jQuery.ajaxSettings.traditional = true;
    $('.timepicker').datetimepicker({timeOnly: true});
    $('.datetimepicker').datetimepicker();
    $('.multiselect').multiselect();
    var frequency = $('#id_frequency');
    var weekdays_row = $(':input[name=weekdays]').parents('tr').addClass('weekdays-row');
    function toggle_weekdays() {
        if (frequency.val() == 'daily') {
            $(weekdays_row).hide();
        } else {
            $(weekdays_row).show();
        }
    }
    if (frequency.length && weekdays_row.length) {
        toggle_weekdays();
        frequency.change(function() {
            toggle_weekdays();
        });
    }
    var feed_type = $('#id_feed_type');
    var url_row = $(':input[name=url]').parents('tr').addClass('weekdays-row');
    function toggle_url() {
        if (feed_type.val() == 'rss' || feed_type.val() == 'atom') {
            $(url_row).show();
        } else {
            $(url_row).hide();
        }
    }
    if (feed_type.length && url_row.length) {
        toggle_url();
        feed_type.change(function() {
            toggle_url();
        });
    }
    $('#tabs li.app-reminders').addClass('active');
});
