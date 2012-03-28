//google.load('visualization', '1', {'packages':['annotatedtimeline']});
//google.setOnLoadCallback(drawChart);
//function drawChart() {
//    var data = new google.visualization.DataTable();
//    data.addColumn('date', 'Date');
//    data.addColumn('number', 'Number of Pills');
//    var rows =[];
//    $('#history-table tbody tr').each(function(i, row) {
//        var dateCell = $(row).find('.date').eq(0);
//        var countCell = $(row).find('.count').eq(0);
//        var date = '';
//        var month = '';
//        var day = '';
//        var year = '';
//        var count = 0;
//        if (dateCell.length) {
//            month = $(dateCell).data('month') - 1;
//            day = $(dateCell).data('day');
//            year = $(dateCell).data('year');
//            date = new Date(year, month, day);
//        }
//        if (countCell.length) {
//            count = $(countCell).data('count');
//        }
//        if (date) {
//            rows.push([date, count]);
//        }
//    });
//    data.addRows(rows);
//    var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('history-chart'));
//    chart.draw(data, {displayAnnotations: false});
//}
