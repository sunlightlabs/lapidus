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
    
    $('th').on('click', 'a[href^="#"]', function(event) {
        event.preventDefault();
       $('html, body').animate({scrollTop: $( $(this).attr('href') ).offset().top}, 800);
    });
}(jQuery));
