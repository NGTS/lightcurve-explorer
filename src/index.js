var React = require('react');
var ReactDOM = require('react-dom');
var $ = require('jquery-browserify');

var LightcurveVisualiser = React.createClass({
    render: function() {
        return (
            <div></div>
        );
    }
});

ReactDOM.render(
    <LightcurveVisualiser />,
    document.getElementById('visualiser')
);
