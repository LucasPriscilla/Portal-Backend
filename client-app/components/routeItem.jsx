import React    from 'react';
import Moment   from 'moment';


class RouteItem extends React.Component {
    render() {
        return (
            <div onClick={this.props.onClick} className="route-item">
                <div className="title">
                    {Moment.duration({
                        seconds: this.props.route.duration
                    }).humanize()}
                </div>
                <div className="subtitle">
                    ${this.props.route.cost.toFixed(2)}<br/>
                    {this.getStartTime()} - {this.getEndTime()}
                </div>
                <div className="align-right">
                    {this.renderModes()}
                </div>
            </div>
        );
    }

    renderModes() {
        return this.props.route.modes.map((mode, index) => {
            return (
                <img key={index} className="icon" src={RouteItem.imageUrlForMode(mode)} />
            )
        })
    }

    getStartTime() {
        return Moment.unix(this.props.route.start_time).local().format("h:mm A");
    }

    getEndTime() {
        return Moment.unix(this.props.route.start_time).add(this.props.route.duration, 'seconds').local().format("h:mm A");
    }

    static imageUrlForMode(mode) {
        if (mode == 'uber') {
            return '/img/uber.png';
        } else if (mode == 'transit') {
            return '/img/transit.png';
        } else {
            return '/img/walking.png';
        }
    }
}

export default RouteItem;