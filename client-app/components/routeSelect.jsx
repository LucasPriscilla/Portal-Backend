import API          from '../services/api';
import EmptyState   from './emptyState';
import PlaceInput   from './placeInput';
import React        from 'react';
import RouteItem    from './routeItem';
import Spinner      from 'react-spinner';


class RouteSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            routes: [],
            error: false
        };
    }

    render() {
        return (
            <div className="sidebar-contents-container">
                <div className="sidebar-contents">
                    <div className="minimum-height">
                        <PlaceInput callback={this.getPlaceInputCallback()} />
                        {this.state.loading ? <Spinner /> : null}
                        {this.shouldDisplayEmptyState()  ? <EmptyState showError={this.state.error} /> : null}
                        {this.state.routes.map((route, index) => {
                            return (
                                <RouteItem onClick={this.getRouteClickHandler(route)} route={route} key={index} />
                            );
                        })}
                    </div>
                </div>
            </div>
        );
    }

    getRouteClickHandler(route) {
        return () => {
            this.props.onRouteClick(route);
        };
    }
    getPlaceInputCallback() {
        return (fromPlace, toPlace) => {
            if (this.state.pendingRequest) {
                this.state.pendingRequest.abort();
                this.setState({
                    loading: false,
                    routes: []
                });
            }
            if (fromPlace && toPlace) {
                let pendingRequest = API.getRoutes(fromPlace, toPlace, (routes) => {
                    this.setState({
                        loading: false,
                        routes: routes,
                        error: routes.length == 0
                    });
                });
                this.setState({
                    loading: true,
                    routes: [],
                    pendingRequest: pendingRequest
                });
            }
            this.props.onPlaceSelect(fromPlace, toPlace);
        }
    }
    shouldDisplayEmptyState() {
        return (!this.state.routes || !this.state.routes.length > 0) && !this.state.loading;
    }
}

export default RouteSelect;
