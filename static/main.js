$(function() {
    $.getJSON('/binning', function(data) {
        $('#binningvalue').text('Points per bin: ' + data.binning);
    });

    $.getJSON('/data', function(data) {
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
                fetchLC(item.dataIndex, function(data) {
                    var options = {
                        series: {
                            lines: { show: false, },
                            points: { show: true, },
                        },
                    };
                    $.plot('#lcplot', [data], options);
                });

                fetchObjID(item.dataIndex, function(obj_id) {
                    $('#lcname').text('Lightcurve ' + obj_id);
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

