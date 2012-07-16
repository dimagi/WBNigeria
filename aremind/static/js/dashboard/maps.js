ko.bindingHandlers.map_volume = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
        var options = {
            center: new google.maps.LatLng(9.05, 8.35),
            zoom: 5,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        element.map = new google.maps.Map(element, options);
        element.ovl = [];
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

        var bounds = new google.maps.LatLngBounds();
        $.each(active.data.by_clinic, function(i, e) {
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
                map: element.map,
                center: pos,
                radius: 1500 * Math.sqrt(volume)
            };

            var dotOptions = {
                strokeWeight: 0,
                fillColor: '#000000',
                fillOpacity: 0.6,
                map: element.map,
                center: pos,
                radius: 400
            };

            var circle = new google.maps.Circle(circleOptions);
            var dot = new google.maps.Circle(dotOptions);
            element.ovl.push(dot);
            element.ovl.push(circle);

            // var goto_detail = function() {
            //     window.location.href = '/dashboard/pbf/reports/?site=' + facility.id;
            // };

            // google.maps.event.addListener(circle, 'click', goto_detail);
            // google.maps.event.addListener(dot, 'click', goto_detail);
        });
        element.map.fitBounds(bounds);
    }
};
