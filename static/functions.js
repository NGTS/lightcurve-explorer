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


