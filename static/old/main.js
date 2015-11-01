$(function() {
    $.getJSON('/api/binning', function(data) {
        $('#binningvalue').text('Points per bin: ' + data.binning);
    });

    for (var i=0; i<4; i++) {
        $.getJSON('/api/sysrem_basis/' + i, render_sysrem_basis(i));
    }

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
        clear_and_plot('#frmsplot', data, options);

        $('#frmsplot').bind('plotclick', function(event, pos, item) {
            if (item) {
                $.getJSON('/api/object_index/' + item.dataIndex, function(data) {
                    multi_render(data.index);
                });
            }
        });

    }).fail(function() {
        console.log('Error reading plot data');
    });;
});

