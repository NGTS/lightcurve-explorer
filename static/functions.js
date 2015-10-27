function render_plot(elm, colour) {
    return function(data) {
        var options = {
            series: {
                lines: { show: false, },
                points: { show: true, lineWidth: 0 },
            },
        };

        if (colour !== undefined) {
            options.series.points.fillColor = colour;
        } else {
            options.series.points.fillColor = '#000';
        }

        clear_and_plot(elm, data, options);
    }
}

function render_sysrem_basis(i) {
    return function(data) {
            var options = {
                series: {
                    lines: { show: false, },
                    points: { show: true, fillColor: '#ff0000', lineWidth: 0},
                },
            };
            clear_and_plot('#sysrem-' + i, data, options);
        };
}


function fetchFromEndpoint(endpoint, data_index, callback) {
    var slug = endpoint + '/' + data_index;
    $.getJSON(slug, function(data) {
        callback(data.data);
    }).fail(function() {
        console.log('Cannot fetch from endpoint ' + slug);
    });
}

function fetchLC(data_index, hdu, callback) {
    fetchFromEndpoint('/api/lc/' + hdu, data_index, callback);
}

function fetchObjID(data_index, callback) {
    fetchFromEndpoint('/api/obj_id', data_index, callback);
}

function fetchPositions(data_index, callback) {
    fetchFromEndpoint('/api/x', data_index, function(x) {
        fetchFromEndpoint('/api/y', data_index, function(y) {
            callback(x, y);
        });
    });
}

function clear_and_plot(elem, data, options) {
    $(elem).empty();
    $.plot(elem, [data], options);
}


function multi_render(index) {
    var hdus = ['flux', 'tamflux', 'casudet'];
    var elements = ['#rawplot', '#lcplot', '#casuplot'];
    var colours = ['#ff0000', '#00ff00', '#0000ff'];

    for (var i=0; i<hdus.length; i++) {
        var hdu = hdus[i];
        var elm = elements[i];
        var colour = colours[i];

        fetchLC(index, hdu, render_plot(elm, colour));
    }

    fetchObjID(index, function(obj_id) {
        var elem = $('#lcname');
        elem.text('Lightcurve ' + obj_id);
        elem.wrap('<a href="/view/' + index + '"/>');
    });

    fetchFromEndpoint('/api/xs', index, render_plot('#xseries'));
    fetchFromEndpoint('/api/ys', index, render_plot('#yseries'));

    fetchPositions(index, function(x, y) {
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
        clear_and_plot('#xyplot', plotdata, options);
    });
}
