import jQuery      from 'jquery';


export default {
    getRoutes(fromPlace, toPlace, callback) {
        return jQuery.ajax({
            url: "/api/v1/route",
            data: {
                from: fromPlace.geometry.location.lat() + " " +  fromPlace.geometry.location.lng(),
                to: toPlace.geometry.location.lat() + " " +  toPlace.geometry.location.lng()
            }
        }).done(function(data) {
            callback(data);
        });
    }
}
