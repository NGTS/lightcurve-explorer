function fetchLC(data_index) {
    $.getJSON('/lc/' + data_index, function(data) {
        $.getJSON('/obj_id/' + data_index, function(obj_id_data) {
            var options = {
                series: {
                    lines: { show: false, },
                    points: { show: true, },
                },
            };
            $.plot('#lcplot', [data], options);
            $('#lcname').text('Lightcurve ' + obj_id_data.obj_id);
        });
    });
}

function renderPositions(data_index) {
    $.getJSON("/x/" + data_index, function(xdata) {
        $.getJSON("/y/" + data_index, function(ydata) {
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
            var plotdata = [[xdata.data, ydata.data]];
            $.plot('#xyplot', [plotdata], options);
        });
    });
}

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
                fetchLC(item.dataIndex);
                renderPositions(item.dataIndex);
            }
        });

    }).fail(function() {
        console.log('Error reading plot data');
    });;
});

