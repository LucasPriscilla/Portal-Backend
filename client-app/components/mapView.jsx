import React    from 'react';
import Moment   from 'moment';


class MapView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            googleMap: null,
            fromMarker: null,
            toMarker: null,
            routeMarkers: [],
            polylines: []
        };
    }

    render() {
        return (
            <div ref="map" className="map" />
        )
    }

    componentDidMount() {
        let googleMap = new google.maps.Map(this.refs.map, {
            center: {
                lat: 37.7749,
                lng: -122.4194
            },
            zoom: 12
        });
        this.setState({
            googleMap: googleMap
        });
        this.renderMap();
    }

    componentDidUpdate(prevProps, prevState) {
        if (prevProps == this.props) {
            return;
        }
        this.renderMap();
    }

    renderPolylines() {
        let polylines = [];
        if (this.props.steps) {
            this.props.steps.forEach((step) => {
                step.polyline.forEach((path) => {
                    let polyline = new google.maps.Polyline({
                        path: google.maps.geometry.encoding.decodePath(path),
                        strokeColor: '#35495D',
                        map: this.state.googleMap
                    });
                    polylines.push(polyline);
                });
            });
        }
        return polylines;
    }

    renderStepMarkers() {
        let routeMarkers = [];
        if (this.props.steps) {
            this.props.steps.forEach((step, index) => {
                let startTime = Moment.unix(step.start_time).local().format("h:mm A");
                let stepWindow = new google.maps.InfoWindow({
                    content: `<strong class="map-window-title">${startTime}</strong>${step.description}`
                });
                let stepMarker = new google.maps.Marker({
                    map: this.state.googleMap,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        strokeWeight: 1,
                        scale: 7,
                        strokeColor: '#FFFFFF',
                        fillColor: index == 0 ? '#35495D' : '#8A8A8A',
                        fillOpacity: 1
                    },
                    position: {
                        lat: step.start_lat,
                        lng: step.start_lng
                    }
                });

                stepMarker.addListener('click', () => {
                    stepWindow.open(this.state.googleMap, stepMarker);
                });
                routeMarkers.push(stepMarker);
            });
        }
        return routeMarkers;
    }

    renderFromMarker() {
        let fromMarker = null;
        if ((!this.props.steps || this.props.steps.length == 0) && this.props.fromPlace) {
            let fromWindow = new google.maps.InfoWindow({
                content: `<strong class="map-window-title">Start</strong>${this.props.fromPlace.formatted_address}`
            });

            fromMarker = new google.maps.Marker({
                map: this.state.googleMap,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    strokeWeight: 1,
                    scale: 7,
                    strokeColor: '#FFFFFF',
                    fillColor: '#35495D',
                    fillOpacity: 1
                },
                position: {
                    lat: this.props.fromPlace.geometry.location.lat(),
                    lng: this.props.fromPlace.geometry.location.lng()
                },
                title: this.props.fromPlace.formatted_address
            });

            fromMarker.addListener('click', () => {
                fromWindow.open(this.state.googleMap, fromMarker);
            });
        }
        return fromMarker;
    }

    renderToMarker() {
        let toMarker = null;
        if (this.props.toPlace) {
            let toWindow = new google.maps.InfoWindow({
                content: `<strong class="map-window-title">End</strong>${this.props.toPlace.formatted_address}`
            });

            toMarker = new google.maps.Marker({
                map: this.state.googleMap,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    strokeWeight: 1,
                    scale: 7,
                    strokeColor: '#FFFFFF',
                    fillColor: '#49A3DF',
                    fillOpacity: 1
                },
                position: {
                    lat: this.props.toPlace.geometry.location.lat(),
                    lng: this.props.toPlace.geometry.location.lng()
                }
            });

            toMarker.addListener('click', () => {
                toWindow.open(this.state.googleMap, toMarker);
            });
        }
        return toMarker;
    }

    clearMarkers() {
        if (this.state.fromMarker) {
            this.state.fromMarker.setMap(null);
        }
        if (this.state.toMarker) {
            this.state.toMarker.setMap(null);
        }

        this.state.routeMarkers.forEach((marker) => {
            marker.setMap(null);
        });

        this.state.polylines.forEach((polyline) => {
            polyline.setMap(null);
        });
    }

    renderMap() {
        this.clearMarkers();

        let routeMarkers = this.renderStepMarkers();
        let fromMarker = this.renderFromMarker() || routeMarkers[0];
        let toMarker = this.renderToMarker();
        let polylines = this.renderPolylines();

        this.setState({
            fromMarker: fromMarker,
            toMarker: toMarker,
            routeMarkers: routeMarkers,
            polylines: polylines
        });
        this.repositionMap(fromMarker, toMarker, routeMarkers, polylines);
    }

    repositionMap(fromMarker, toMarker, markers, polylines) {
        if (this.props.selectedStep) {
            this.state.googleMap.panTo({
                lat: this.props.selectedStep.start_lat,
                lng: this.props.selectedStep.start_lng
            });
        } else if (this.props.fromPlace && !this.props.toPlace) {
            this.state.googleMap.panTo({
                lat: this.props.fromPlace.geometry.location.lat(),
                lng: this.props.fromPlace.geometry.location.lng()
            });
        } else if (!this.props.fromPlace && this.props.toPlace) {
            this.state.googleMap.panTo({
                lat: this.props.toPlace.geometry.location.lat(),
                lng: this.props.toPlace.geometry.location.lng()
            });
        } else if (this.props.fromPlace && this.props.toPlace) {
            let combinedMarkers = [fromMarker, toMarker].concat(markers);
            let bounds = new google.maps.LatLngBounds();
            combinedMarkers.forEach((marker) => {
                bounds.extend(marker.getPosition());
            });
            polylines.forEach((polyline) => {
                polyline.getPath().forEach((position) => {
                    bounds.extend(position);
                });
            });
            this.state.googleMap.fitBounds(bounds);
        }
    }
}

export default MapView;
 