$(function() {
    var lc_id = $('h1#obj_id').data('index');
    fetchObjID(lc_id, function(obj_id) {
        $('h1#obj_id').text(obj_id);
    });

    fetchLC(lc_id, function(data) {
        var options = {
            series: {
                lines: { show: false, },
                points: { show: true, },
            },
        };
        $.plot('#lcplot', [data], options);
    });

});
