var bounds = new google.maps.LatLngBounds();
var map_element = null;

function addMarker(e, onclick) {
    var facility = e[0];
    var volume = e[1];

    if (facility == null) {
        return;
    }

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

    if (onclick) {
	var _onclick = function() { return onclick(facility); };
	google.maps.event.addListener(circle, 'click', _onclick);
	google.maps.event.addListener(dot, 'click', _onclick);
    }

    var onhover = function(in_) {
	circle.setOptions({
		strokeColor: in_ ? "#ff0" : '#DA4F49',
		fillColor: in_ ? '#ff0' : '#DA4F49', 
	    });
	site_name(in_ ? facility.name : null, map_element.map);
    };
    google.maps.event.addListener(circle, 'mouseover', function() { onhover(true); });
    google.maps.event.addListener(circle, 'mouseout', function() { onhover(false); });
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
            var goto_detail = function(facility) {
                window.location.href = DETAIL_URL + '?site=' + facility.id;
            };
            
            var data = active.data.by_clinic;
            var add_marker = function(i, e) { addMarker(e, goto_detail); };
        } else {
            var select_clinic = function(facility) {
                var clinic = viewModel.facility_by_id(facility.id);
                viewModel.active_metric('satisf');
                viewModel.active_facility(clinic);
            };
            
            var data = active.clinic_totals;
            var add_marker = function(i, e) { addMarker(e, select_clinic); };
        }
        $.each(data, add_marker);
        
        google.maps.event.addListenerOnce(element.map, 'bounds_changed', function(event) {
                var MAX_ZOOM = 12;
                if (element.map.getZoom() > MAX_ZOOM) {
                    element.map.setZoom(MAX_ZOOM);
                }
            });
        element.map.fitBounds(bounds);
    }
};
