$(function() {
    var lc_id = $('h1#obj_id').data('index');
    fetchObjID(lc_id, function(obj_id) {
        $('h1#obj_id').text(obj_id);
    });
});
