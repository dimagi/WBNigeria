$(document).ready(function() {
    $('.timepicker').datetimepicker({timeOnly: true});
    $('.datepicker').datepicker({dateFormat: 'yy-mm-dd'});
    $('#tabs li.app-patients').addClass('active');
});
