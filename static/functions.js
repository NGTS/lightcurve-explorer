function fetchLC(data_index, callback) {
    $.getJSON('/lc/' + data_index, function(data) {
        callback(data);
    });
}

function fetchObjID(data_index, callback) {
    $.getJSON('/obj_id/' + data_index, function(obj_id_data) {
        callback(obj_id_data.obj_id);
    });
}

function fetchPositions(data_index, callback) {
    $.getJSON("/x/" + data_index, function(xdata) {
        $.getJSON("/y/" + data_index, function(ydata) {
            callback(xdata.data, ydata.data);
        });
    });
}


