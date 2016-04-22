import React    from 'react';


class PlaceInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            fromPlace: null
        };
    }

    render() {
        return (
            <div className="place-input">
                <div className="group">
                    <div className="group-label">
                        START
                    </div>
                    <input disabled={this.props.disabled} ref="from"
                           value={this.state.fromPlace !== null ? this.state.fromPlace.formatted_address : null}
                           placeholder="" type="text" />
                </div>
                <div className="group">
                    <div className="group-label">
                        END
                    </div>
                    <input disabled={this.props.disabled} ref="to" placeholder="" type="text" />
                </div>
            </div>
        );
    }

    componentDidMount() {
        let fromAutocomplete = new google.maps.places.Autocomplete(this.refs.from, {types: ['geocode']});
        fromAutocomplete.addListener('place_changed', this.getFromPlaceListener());

        let toAutocomplete = new google.maps.places.Autocomplete(this.refs.to, {types: ['geocode']});
        toAutocomplete.addListener('place_changed', this.getToPlaceListener());

        this.setState({
            fromAutocomplete: fromAutocomplete,
            toAutocomplete: toAutocomplete
        });
        this.configureUserLocation();
    }

    configureUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                var geolocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                var circle = new google.maps.Circle({
                    center: geolocation,
                    radius: position.coords.accuracy
                });
                var geocoder = new google.maps.Geocoder;
                geocoder.geocode({'location': geolocation}, (results, status) => {
                    if (!this.state.fromPlaceChanged && status === google.maps.GeocoderStatus.OK) {
                        if (results[0]) {
                            let fromPlace = results[0];
                            this.setState({
                                fromPlace: fromPlace,
                                fromPlaceChanged: true
                            });
                            this.props.callback(fromPlace, this.state.toPlace);
                        }
                    }
                });
                this.state.fromAutocomplete.setBounds(circle.getBounds());
                this.state.toAutocomplete.setBounds(circle.getBounds());
            });
        }
    }

    getFromPlaceListener() {
        return () => {
            let fromPlace = this.state.fromAutocomplete.getPlace();
            if (!fromPlace.geometry) {
                fromPlace = null;
            }

            this.setState({
                fromPlace: fromPlace,
                fromPlaceChanged: true
            });
            this.props.callback(this.state.fromPlace, this.state.toPlace);
        };
    }

    getToPlaceListener() {
        return () => {
            let  toPlace = this.state.toAutocomplete.getPlace();
            if (!toPlace.geometry) {
                toPlace = null;
            }

            this.setState({
                toPlace: toPlace
            });
            this.props.callback(this.state.fromPlace, this.state.toPlace);
        };
    }
}

export default PlaceInput;
