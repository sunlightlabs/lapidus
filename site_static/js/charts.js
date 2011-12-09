jQuery(document).ready(function($) {
    var options = {
        colors: ["#274868"],
        series: {
          lines:  { show: true, lineWidth: 3 },
          points: { show: true, radius: 4, symbol: "circle" }
        },
        xaxis: { mode: "time", show: false },
        grid: {
            hoverable: true,
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
                        var time = new Date(item.datapoint[0]).toDateString(),
                            y = $($(elem).find('table.data-table tr.datapoint')[item.dataIndex].children[1]).text(); // Drew did it.

                        showTooltip(item.pageX, item.pageY, time + ": <strong>" + y + "</strong>");
                    }
                }
                else {
                    $("#tooltip").remove();
                    previousPoint = null;            
                }
            });
            $(element).find('.table-wrapper').hide();
            
        }
    });
    
    $('.table-toggle > a').on("click", function(event) {
        console.log( event );
        $($(this).attr('href')).slideToggle();
        event.preventDefault();
    });
    
});
