var page = require('webpage').create();
page.viewportSize = { width: 1024, height: 768 };

page.open('http://localhost:5000/', function() {
    page.render('screenshots/screenshot-landing.png');
    page.open('http://localhost:5000/view/14289', function() {
        page.render('screenshots/screenshot-detail.png');
        phantom.exit();
    });
});


