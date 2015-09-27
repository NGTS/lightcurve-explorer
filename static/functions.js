function fetchFromEndpoint(endpoint, data_index, callback) {
    var slug = endpoint + '/' + data_index;
    $.getJSON(slug, function(data) {
        callback(data.data);
    }).fail(function() {
        console.log('Cannot fetch from endpoint ' + slug);
    });
}

function fetchLC(data_index, callback) {
    fetchFromEndpoint('/lc', data_index, callback);
}

function fetchObjID(data_index, callback) {
    fetchFromEndpoint('/obj_id', data_index, callback);
}

function fetchPositions(data_index, callback) {
    fetchFromEndpoint('/x', data_index, function(x) {
        fetchFromEndpoint('/y', data_index, function(y) {
            callback(x, y);
        });
    });
}


