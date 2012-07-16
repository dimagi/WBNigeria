var bounds = new google.maps.LatLngBounds();
var map_element = null;

function addMarkers(i, e) {
    var facility = e[0];
    var volume = e[1];

    var pos = new google.maps.LatLng(facility.lat, facility.lon);
    bounds.extend(pos);

    var circleOptions = {
        strokeColor: '#DA4F49',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#DA4F49',
        fillOpacity: 0.35,
        map: map_element.map,
        center: pos,
        radius: 1500 * Math.sqrt(volume)
    };

    var dotOptions = {
        strokeWeight: 0,
        fillColor: '#000000',
        fillOpacity: 0.6,
        map: map_element.map,
        center: pos,
        radius: 400
    };

    var circle = new google.maps.Circle(circleOptions);
    var dot = new google.maps.Circle(dotOptions);
    map_element.ovl.push(dot);
    map_element.ovl.push(circle);

    // var goto_detail = function() {
    //     window.location.href = '/dashboard/pbf/reports/?site=' + facility.id;
    // };

    // var select_clinic = function() {
    //     var clinic = viewModel.facility_by_id(facility.id);
    //     viewModel.active_metric('satisf');
    //     viewModel.active_facility(clinic);
    // };

    // google.maps.event.addListener(circle, 'click', goto_detail);
    // google.maps.event.addListener(dot, 'click', goto_detail);

    // google.maps.event.addListener(circle, 'click', select_clinic);
    // google.maps.event.addListener(dot, 'click', select_clinic);
}

ko.bindingHandlers.map_volume = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var options = {
            center: new google.maps.LatLng(9.05, 8.35),
            zoom: 5,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };

        element.map = new google.maps.Map(element, options);
        element.ovl = [];

        // Need a global copy for the moment
        map_element = element;
    },

    update: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var active = ko.utils.unwrapObservable(valueAccessor());
        if (!active) {
            return;
        }

        $.each(element.ovl, function(i, e) {
            e.setMap(null);
        });
        element.ovl = [];

        if(active.data && active.data.by_clinic) {
            $.each(active.data.by_clinic, addMarkers);
        } else {
            $.each(active.clinic_totals, addMarkers);
        }

        element.map.fitBounds(bounds);

        var MAX_ZOOM = 12;

        if (element.map.getZoom() > MAX_ZOOM) {
            element.map.setZoom(MAX_ZOOM);
        }
    }
};
