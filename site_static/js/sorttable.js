(function () {
    $('#analytics').tablesorter({
        sortList: [
            [0, 0]
        ],
        cssChildRow: "secondary",
        widgets: ["zebra"]//,
    });

    $('.secondary').hide();
    $('#analytics').delegate('tbody tr.primary th', 'click', function() {
        $(this).closest('tr').toggleClass('expanded').nextUntil('tr:not(.secondary)').toggle();
        return false;
    });
}());