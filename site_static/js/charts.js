jQuery(document).ready(function($) {
    var dialog_title = $($('#annotation_dialog > h3')[0]).text();
    $($('#annotation_dialog > h3')[0]).hide();
    var annotation_dialog = $('#annotation_dialog').dialog({ resizable: false, width: 400, title:dialog_title, modal: true, autoOpen: false });

    $("#annotation_dialog > form").submit(function(event) {
        var form = $(this);
        var url = form.attr( 'action' );
        var data = form.serializeArray();
        // console.log(form);
        
        $.post(url, data, function(data, textStatus, jqXHR) {
            if (console) console.log(textStatus);
        });
        
        event.preventDefault();
        return false;
    });

    
    var options = {
        colors: ["#274868"],
        series: {
          lines:  { show: true, lineWidth: 3 },
          points: { show: true, radius: 4, symbol: "circle" }
        },
        xaxis: { mode: "time", show: false },
        grid: {
            hoverable: true,
            clickable: true,
            borderColor: "#E1DFDA"
        }
      };
    
    function showTooltip(x, y, contents) {
            $('<div id="tooltip">' + contents + '</div>').css( {
                position: 'absolute',
                display: 'none',
                top: y - 35,
                left: x -20,
                border: '1px solid #EEE',
                padding: '2px',
                'background-color': '#FFF',
                opacity: 0.80
            }).appendTo("body").fadeIn(200);
    }
    
    $('section.unit-observations').each(function(index, element) {
        var data = [];
        var chart = $(element).find('div.chart');
        if (chart.length !== 0) {
            $(element).find('table.data-table tr.datapoint').each(function(index, subelement) {
                data.push([ Number( $(subelement).find('time').first().attr('data-milliseconds') ),
                            Number( $(subelement).find('.observation').attr('data-value') )
                            ]);
            });
            var plot = $.plot($(element).find('div.chart'), [data], options);
            var previousPoint = null;
        
            $(chart).bind("plothover", function (event, pos, item) {
                if (item) {
                    var elem = element;

                    if (previousPoint != item.dataIndex) {
                        previousPoint = item.dataIndex;
                        
                        $("#tooltip").remove();
                        var time = $($(elem).find('table.data-table tr.datapoint')[item.dataIndex].children[0]).text(),
                            y = $($(elem).find('table.data-table tr.datapoint')[item.dataIndex].children[1]).text(); // Drew did it.

                        showTooltip(item.pageX, item.pageY, time + ": <strong>" + y + "</strong>");
                    }
                }
                else {
                    $("#tooltip").remove();
                    previousPoint = null;            
                }
            });
            
            $(chart).bind("plotclick", function(event, pos, item) {
                var elem = element;
                var time_el = $($(elem).find('table.data-table tr.datapoint')[item.dataIndex].children[0]).find('time')[0];
                var time = $(time_el).attr('datetime');
                console.log(time);
                $(annotation_dialog).find('#id_timestamp')[0].value = time.replace('T', ' ');
                $(annotation_dialog).dialog('open');
            });
            
            $(element).find('.table-wrapper').hide();
            
        }
    });
    
    $('.table-toggle > a').on("click", function(event) {
        $($(this).attr('href')).slideToggle();
        event.preventDefault();
    });
    
});
