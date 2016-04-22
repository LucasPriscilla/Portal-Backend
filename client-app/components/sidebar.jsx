import React        from 'react';
import RouteModal   from './routeModal';
import RouteSelect  from './routeSelect';


class Sidebar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            selectedRoute: null,
            showRouteModal: false,
            routes: []
        };
    }

    render() {
        return (
            <div ref="sidebar" className="sidebar">
                <RouteSelect onPlaceSelect={this.props.placeSelectedCallback}
                             onRouteClick={this.getRouteClickHandler()} />
                <RouteModal onClose={this.getCloseModalHandler()}
                            onRouteClick={this.getSelectedRouteClickHandler()}
                            onStepClick={this.getStepClickHandler()} route={this.state.selectedRoute}
                            showModal={this.state.showRouteModal} />
            </div>
        )
    }

    getSelectedRouteClickHandler() {
        return () => {
            this.props.routeSelectedCallback(this.state.selectedRoute);
        };
    }

    getCloseModalHandler() {
        return () => {
            this.setState({
                showRouteModal: false
            });
            this.props.routeSelectedCallback(null);
        };
    }

    shouldDisplayRouteModal() {
        return this.state.selectedRoute !== null;
    }

    getStepClickHandler() {
        return (step) => {
            this.props.stepSelectedCallback(step);
        }
    }

    getRouteClickHandler() {
        return (route) => {
            this.setState({
                selectedRoute: route,
                showRouteModal: true
            });
            this.props.routeSelectedCallback(route);
        }
    }
}

export default Sidebar;
