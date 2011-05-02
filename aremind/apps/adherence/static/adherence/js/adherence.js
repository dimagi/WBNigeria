$(document).ready(function() {
    jQuery.ajaxSettings.traditional = true;
    $('.timepicker').datetimepicker({timeOnly: true});
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
});
