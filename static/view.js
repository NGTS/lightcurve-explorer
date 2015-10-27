$(function() {
    var lc_id = $('h1#obj_id').data('index');

    fetchObjID(lc_id, function(obj_id) {
        $('h1#obj_id').text(obj_id);
    });

    multi_render(lc_id);

    for (var i=0; i<4; i++) {
        $.getJSON('/api/sysrem_basis/' + i, render_sysrem_basis(i));
    }
});
