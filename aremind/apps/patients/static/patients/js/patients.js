$(document).ready(function() {
    $('.timepicker').datetimepicker({timeOnly: true});
    $('.datepicker').datepicker({dateFormat: 'yy-mm-dd'});
    $('#tabs li.app-patients').addClass('active');
    $('.monthpicker').hide();
    $('label[for="id_fakedate"]').hide()
    $('.fakedate').datepicker( {
            changeMonth: true,
            changeYear: true,
            showButtonPanel: true,
            dateFormat: 'MM yy',
            altField: '.monthpicker',
            altFormat: 'yy-mm-dd',
            onClose: function(dateText, inst) {
                var month = $("#ui-datepicker-div .ui-datepicker-month :selected").val();
                var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
                $(this).datepicker('setDate', new Date(year, month, 1));
            }
        });
});
