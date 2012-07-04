var locations = {
    'one': {
        'latlng': new google.maps.LatLng(7.8219, 6.9743),
        'radius': 15000
    },
    'two': {
        'latlng': new google.maps.LatLng(7.6219, 7.4743),
        'radius': 8000
    },
    'three': {
        'latlng': new google.maps.LatLng(7.2219, 6.4743),
        'radius': 18000
    }
};

var options = {
    center: new google.maps.LatLng(7.6219, 6.9743),
    zoom: 8,
    mapTypeId: google.maps.MapTypeId.ROADMAP
};

var map = new google.maps.Map(document.getElementById('map'), options);

for(var loc in locations) {
    var circleOptions = {
        strokeColor: '#DA4F49',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#DA4F49',
        fillOpacity: 0.35,
        map: map,
        center: locations[loc].latlng,
        radius: locations[loc].radius
    };

    var dotOptions = {
        strokeColor: '#000000',
        strokeOpacity: 1.0,
        strokeWeight: 1,
        fillColor: '#000000',
        fillOpacity: 1.0,
        map: map,
        center: locations[loc].latlng,
        radius: 1600
    };

    var circle = new google.maps.Circle(circleOptions);
    var dot = new google.maps.Circle(dotOptions);
}