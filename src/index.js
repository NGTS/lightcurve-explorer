var React = require('react');
var ReactDOM = require('react-dom');
var $ = require('jquery-browserify');
var plot = require('./flot-shim');


var SysremBasisFunction = React.createClass({
    getInitialState: function() {
        return {data: []};
    },

    componentDidMount: function() {
        $.getJSON('/api/sysrem_basis/' + this.props.index, function(data) {
            this.setState({data: data.data});
        }.bind(this));
    },

    content: function() {
        if (!this.state.data) {
            return <p>Loading</p>;
        } else {
            return <div className="plot" id={"sysrem-" + this.props.index}></div>;
        }
    },

    componentDidUpdate: function() {
        var options = {
            series: {
                lines: { show: false, },
                points: { show: true, fillColor: '#ff0000', lineWidth: 0},
            },
        };
        plot('#sysrem-' + this.props.index, [this.state.data], options);
    },

    render: function() {
        return (
            <div className="basis-function col-md-3">
            {this.content()}
            </div>
        );
    }
});

var SysremBasisFunctions = React.createClass({
    render: function() {
        return (
            <div className="row sysrem-basis-functions">
            <h3>Sysrem basis functions</h3>
            {[0, 1, 2, 3].map(function(index) {
                return <SysremBasisFunction index={index} />
            })}
            </div>
        );
    }
});

var LightcurveVisualiser = React.createClass({
    render: function() {
        return (
            <div className="lightcurve-visualiser">
            <h1>Lightcurve visualiser</h1>
            <SysremBasisFunctions />
            </div>
        );
    }
});

ReactDOM.render(
    <LightcurveVisualiser />,
    document.getElementById('visualiser')
);
