/* Author: Daniel Cloud

*/
(function() {
    var sparkWidth = $(".visits.metric").width();
    var sparkHeight = $(".visits.metric").height();
    // var data = [6, 4, 4, 4, 5, 4, 5, 5, 5, 5, 4, 3, 3, 3, 5, 3, 6, 8, 8, 10, 8, 5, 5, 5];
    
    var data = [[0, 6], [1, 4], [2, 4], [3, 4], [4, 5], [5, 4], [6, 5], [7, 5], [8, 5], [9, 5], [10, 4], [11, 3], [12, 3], [13, 3], [14, 5], [15, 3], [16, 6], [17, 8], [18, 8], [19, 10], [20, 8]];
    
    $('.metric').each(function() {
        $.plot($(this), [data], {
            series: {
                  lines: { show: true, lineWidth: 1 },
                  color: "#72A6D8",
                  shadowSize: 0
            },
            legend: { show: false },
            xaxis: { ticks: [] },
            yaxis: { ticks: [], min: 0 },
            selection: { mode: "x" },
            grid: {
                borderWidth: 0
            }
        });
    });

    $('#analytics').tablesorter({
        sortList: [
            [0, 0]
        ],
        cssChildRow: "secondary",
        widgets: ["zebra"]//,
/*
        headers: {
            7: {
                sorter: false
            }
        }
*/
    });

    $('.secondary').hide();
    $('#analytics').delegate('tbody tr th:first-child', 'click', function() {
        $(this).closest('tr').toggleClass('expanded').nextUntil('tr:not(.secondary)').toggle();
        return false;
    });

}(jQuery));
