/* Author: Daniel Cloud

*/
(function() {

    $( ".datefield" ).datepicker({
        dateFormat: 'yy-mm-dd',
        maxDate: MAX_DATE,
        changeMonth: true,
        changeYear: true
    });
    var dfFrom = $( ".datefield" ).eq(0);
    var dfTo =  $( ".datefield" ).eq(1);
    dfFrom.datepicker("option", "onClose", function(dateText, inst) 
    {   
        fromDate = dfFrom.datepicker("getDate");
        toDate = dfTo.datepicker("getDate");
        console.log("From " + fromDate + " to " + toDate);
        if (fromDate > toDate) dfTo.datepicker("setDate", fromDate);
    });
    dfTo.datepicker("option", "onClose", function(dateText, inst) {
        fromDate = dfFrom.datepicker("getDate");
        toDate = dfTo.datepicker("getDate");
        console.log("From " + fromDate + " to " + toDate);
        if (fromDate > toDate) dfFrom.datepicker("setDate", toDate);
    });
    $('#analytics').tablesorter({
        sortList: [
            [0, 0]
        ],
        cssChildRow: "secondary",
        widgets: ["zebra"]//,
    });

    $('.secondary').hide();
    $('#analytics').delegate('tbody tr th:first-child', 'click', function() {
        $(this).closest('tr').toggleClass('expanded').nextUntil('tr:not(.secondary)').toggle();
        return false;
    });

}(jQuery));
