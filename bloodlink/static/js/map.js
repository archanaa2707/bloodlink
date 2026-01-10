// Map initialization and location handling

let map;
let marker;

function initMap(lat = 17.4065, lng = 78.4772) {
    // Default location: Hyderabad
    if (document.getElementById('map')) {
        map = L.map('map').setView([lat, lng], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);
        
        marker = L.marker([lat, lng], {
            draggable: true
        }).addTo(map);
        
        marker.on('dragend', function(e) {
            const position = marker.getLatLng();
            updateLocationInputs(position.lat, position.lng);
        });
        
        map.on('click', function(e) {
            marker.setLatLng(e.latlng);
            updateLocationInputs(e.latlng.lat, e.latlng.lng);
        });
    }
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                if (map) {
                    map.setView([lat, lng], 13);
                    marker.setLatLng([lat, lng]);
                } else {
                    initMap(lat, lng);
                }
                
                updateLocationInputs(lat, lng);
            },
            function(error) {
                alert('Error getting location: ' + error.message);
                initMap(); // Initialize with default location
            }
        );
    } else {
        alert('Geolocation is not supported by your browser');
        initMap(); // Initialize with default location
    }
}

function updateLocationInputs(lat, lng) {
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;
    
    // Reverse geocoding using Nominatim (OpenStreetMap)
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
            const address = data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            document.getElementById('address').value = address;
        })
        .catch(error => {
            console.error('Geocoding error:', error);
            document.getElementById('address').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        });
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('map')) {
        initMap();
    }
});