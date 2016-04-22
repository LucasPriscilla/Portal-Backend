import React    from 'react';
import MapView  from './mapView';
import Sidebar  from './sidebar';

class MainView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            fromPlace: null,
            toPlace: null
        };
    }
    
    render() {
        return (
            <div className="main">
                <MapView selectedStep={this.state.selectedStep}
                         steps={this.state.selectedRoute ? this.state.selectedRoute.steps : null}
                         fromPlace={this.state.fromPlace}
                         toPlace={this.state.toPlace} />
                <Sidebar stepSelectedCallback={this.getStepSelectedCallback()}
                         routeSelectedCallback={this.getRouteSelectedCallback()}
                         placeSelectedCallback={this.getPlaceSelectedCallback()} />
            </div>
        )
    }

    getRouteSelectedCallback() {
        return (route) => {
            this.setState({
                selectedRoute: route,
                selectedStep: null
            });
        }
    }

    getStepSelectedCallback() {
        return (step) => {
            this.setState({
                selectedStep: step
            });
        }
    }

    getPlaceSelectedCallback() {
        return (fromPlace, toPlace) => {
            this.setState({
                fromPlace: fromPlace,
                toPlace: toPlace,
                selectedRoute: null,
                selectedStep: null
            })
        };
    }
}

export default MainView;
