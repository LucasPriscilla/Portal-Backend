import Classnames                   from 'classnames';
import CloseButton                  from './closeButton.jsx'
import React                        from 'react';
import RouteItem                    from './routeItem';
import StepItem                     from './stepItem';
import {TransitionMotion, spring}   from 'react-motion';

class RouteModal extends React.Component {
    static willEnter() {
        return {
            opacity: 0
        };
    }

    static willLeave() {
        return {
            opacity: spring(0)
        };
    }

    getModalStyles() {
        return this.props.showModal ? [{
            key: 1,
            style: {
                opacity: spring(1)
            }
        }] : [];
    }

    render() {
        return (
            <TransitionMotion styles={this.getModalStyles()} willEnter={RouteModal.willEnter}
                              willLeave={RouteModal.willLeave}>
                {([interpolatedStyle]) => (
                    interpolatedStyle ?
                        <div className={Classnames("sidebar-contents-container",
                                {"disable-interaction": !this.props.showModal})}
                             style={interpolatedStyle.style}>
                            <div className="sidebar-contents">
                                <CloseButton onClick={this.props.onClose} />
                                <RouteItem onClick={this.props.onRouteClick} route={this.props.route} />
                                <div className="separator" />
                                {this.props.route.steps.map((step, index) => {
                                    return (
                                        <StepItem onClick={this.getStepClickHandler(step)} step={step} key={index} />
                                    );
                                })}
                            </div>
                        </div> : null
                )}
            </TransitionMotion>
        );
    }

    getStepClickHandler(step) {
        return () => {
            this.props.onStepClick(step);
        };
    }
}

export default RouteModal;
