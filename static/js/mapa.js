
//  Inicializar el mapa centrado en Chile
const map = L.map('map', {
    zoomControl: false
}).setView([-33.4489, -70.6693], 6);
// B. Cargar la capa base abierta de ESRI (100% libre y sin API Key)
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
    maxZoom: 18
}).addTo(map);
estaciones.forEach(est => {
    const marker = L.circleMarker([est.lat, est.lon], {
        radius: 10,
        fillColor: est.color,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);

    marker.bindPopup(`
        <div style="font-family: sans-serif; min-width: 150px;">
            <h6 style="margin: 0 0 5px 0; font-weight: bold;">${est.estacion}</h6>
            <span style="background: ${est.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                ${est.estado}
            </span>
            <p style="margin: 8px 0 0 0; font-size: 0.85rem;">
                <strong>${est.parametro}:</strong> ${est.valor} ${est.unidad}
            </p>
            <small style="color: gray;">${est.fecha}</small>
        </div>
        `);
});

// Lógica del Buscador: buscar lugares en Chile usando la API Nominatim
const inputBuscar = document.getElementById('inputBuscar');
let marcadorBusqueda = null;
inputBuscar.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        const lugar = inputBuscar.value.trim();
        if (!lugar) return;

        // Consultamos la API pública restringida a Chile (countrycodes=cl)
        const url = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=cl&q=${encodeURIComponent(lugar)}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && data.length > 0) {
                    const primerResultado = data[0];
                    const lat = parseFloat(primerResultado.lat);
                    const lon = parseFloat(primerResultado.lon);

                    // Vuela suavemente hacia el lugar encontrado
                    map.flyTo([lat, lon], 13, { duration: 1.5 });

                    // Si ya había un marcador de búsqueda anterior, lo quitamos
                    if (marcadorBusqueda) {
                        map.removeLayer(marcadorBusqueda);
                    }

                    // Ponemos un marcador con el nombre del lugar
                    marcadorBusqueda = L.marker([lat, lon]).addTo(map)
                        .bindPopup(`<b>${primerResultado.display_name}</b>`)
                        .openPopup();
                } else {
                    alert("No encontramos ese lugar en Chile. Intenta con otra comuna o ciudad.");
                }
            })
            .catch(err => {
                console.error("Error al buscar:", err);
                alert("Hubo un problema al buscar la ubicación.");
            });
    }
});