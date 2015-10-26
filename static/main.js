function render_plot(elm) {
    return function(data) {
        var options = {
            series: {
                lines: { show: false, },
                points: { show: true, },
            },
        };
        $.plot(elm, [data], options);
    }
}


$(function() {
    $.getJSON('/api/binning', function(data) {
        $('#binningvalue').text('Points per bin: ' + data.binning);
    });

    $.getJSON('/api/data', function(data) {
        var options = {
            series: {
                lines: { show: false, },
                points: { show: true, },
            },
            grid: {
                clickable: true,
            },
        };
        $.plot('#frmsplot', [data], options);

        $('#frmsplot').bind('plotclick', function(event, pos, item) {
            if (item) {
                var hdus = ['flux', 'tamflux', 'casudet'];
                var elements = ['#rawplot', '#lcplot', '#casuplot'];

                for (var i=0; i<hdus.length; i++) {
                    var hdu = hdus[i];
                    var elm = elements[i];

                    fetchLC(item.dataIndex, hdu, render_plot(elm));
                }

                fetchObjID(item.dataIndex, function(obj_id) {
                    var elem = $('#lcname');
                    elem.text('Lightcurve ' + obj_id);
                    elem.wrap('<a href="/view/' + item.dataIndex + '"/>');
                });

                fetchPositions(item.dataIndex, function(x, y) {
                    var options = {
                        xaxis: {
                            min: 0,
                            max: 2047,
                        },
                        yaxis: {
                            min: 0,
                            max: 2047,
                        },
                        series: {
                            lines: { show: false },
                            points: {
                                show: true,
                                radius: 10,
                                symbol: 'circle',
                            },
                        },
                    };
                    var plotdata = [[x, y]];
                    $.plot('#xyplot', [plotdata], options);
                });
            }
        });

    }).fail(function() {
        console.log('Error reading plot data');
    });;
});

