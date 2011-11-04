jQuery(document).ready(function($) {
    // Bits stolen! from django source
    var tbody = "#orderedmembership_set-group .tabular.inline-related tbody";
    var row = 'tr.has_original.dynamic-orderedmembership_set';
    var rows = tbody + ' ' + row;
    var alternatingRows = function(row) {
        $(rows).not(".add-row").removeClass("row1 row2")
            .filter(":even").addClass("row1").end()
            .filter(rows + ":odd").addClass("row2");
    };
    
    $(tbody).sortable({
        containment: 'parent',
        items: row,
        create: function(event, ui) {
            $(rows).children('td').each(function(index) {
                $(this).attr('width', $(this).width());
            });
        },
        update: function(event, ui) {
            alternatingRows();
            
            $(this).find(row).each(function(index) {
                $(this).find('td.order input').val(index);
            });
        }
    });
    
});
