var page = require('webpage').create();
page.viewportSize = { width: 1024, height: 768 };

/* Stolen from http://stackoverflow.com/a/4288992/56711 */
function asyncLoop(iterations, func, callback) {
    var index = 0;
    var done = false;
    var loop = {
        next: function() {
            if (done) {
                return;
            }

            if (index < iterations) {
                index++;
                func(loop);

            } else {
                done = true;
                callback();
            }
        },

        iteration: function() {
            return index - 1;
        },

        break: function() {
            done = true;
            callback();
        }
    };
    loop.next();
    return loop;
}

var objects = [13567, 16161, 4738, 7547];

asyncLoop(objects.length, function(loop) {
    var o = objects[loop.iteration()];
    var url = 'http://localhost:5000/view/' + o;
    console.log('Rendering ' + url);
    var outname = '/tmp/aperture-' + o + '.png';
    page.open(url, function() {
        page.render(outname);
        loop.next();
    });
}, function() {
    phantom.exit();
});
