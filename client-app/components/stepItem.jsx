import React    from 'react';
import Moment   from 'moment';


class StepItem extends React.Component {
    render() {
        return (
            <div onClick={this.props.onClick} className="step-item">
                <div className="title">
                    {this.props.step.description}
                </div>
                <div className="subtitle">
                    ${this.props.step.cost.toFixed(2)}<br/>
                    {this.getStartTime()} - {this.getEndTime()}
                    {this.props.step.start_time !== this.props.step.departure_time ? this.renderDepartureTime() : null}
                </div>
                <div className="align-right">
                    <img className="icon" src={StepItem.imageUrlForMode(this.props.step.mode)} />
                </div>
            </div>
        );
    }

    renderDepartureTime() {
        return (
            <span>
                <br/>
                Departs at {this.getDepartureTime()}
            </span>
        );
    }

    getStartTime() {
        return Moment.unix(this.props.step.start_time).local().format("h:mm A");
    }

    getEndTime() {
        return Moment.unix(this.props.step.start_time).add(this.props.step.duration, 'seconds').local().format("h:mm A");
    }

    getDepartureTime() {
        return Moment.unix(this.props.step.departure_time).local().format("h:mm A");
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

export default StepItem;