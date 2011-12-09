(function () {
    $('#analytics').tablesorter({
        sortList: [
            [0, 0]
        ],
        cssChildRow: "secondary",
        widgets: ["zebra"]//,
    });
    // Hide secondary rows and set up toggle event on th
    $('.secondary').hide();
    $('#analytics').on('click', 'tbody tr.primary th', function() {
        $(this).closest('tr').toggleClass('expanded').nextUntil('tr:not(.secondary)').toggle();
        return false;
    });
    // Prevent anchors in th from propogating event so default can occur rather than toggle event.
    $('#analytics').on('click', 'tbody tr.primary a', function() {
        event.stopPropagation();
    });
}());