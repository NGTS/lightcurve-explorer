var React = require('react');
var ReactDOM = require('react-dom');
var $ = require('jquery-browserify');

var HelloWorld = React.createClass({
    render: function() {
        return (
            <p>Hello world</p>
        );
    }
});

ReactDOM.render(
    <HelloWorld />,
    document.getElementById('visualiser')
);
