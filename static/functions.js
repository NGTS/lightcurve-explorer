function fetchLC(data_index, callback) {
    $.getJSON('/lc/' + data_index, function(data) {
        callback(data);
    }).fail(function() {
        console.log('Cannot fetch lightcurve for object ' + data_index);
    });
}

function fetchObjID(data_index, callback) {
    $.getJSON('/obj_id/' + data_index, function(obj_id_data) {
        callback(obj_id_data.obj_id);
    }).fail(function() {
        console.log('Cannot fetch object id for object ' + data_index);
    });
}

function fetchPositions(data_index, callback) {
    $.getJSON("/x/" + data_index, function(xdata) {
        $.getJSON("/y/" + data_index, function(ydata) {
            callback(xdata.data, ydata.data);
        }).fail(function() {
            console.log('Cannot fetch y position for object ' + data_index);
        });
    }).fail(function() {
        console.log('Cannot fetch x position for object ' + data_index);
    });
}


