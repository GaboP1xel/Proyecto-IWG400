// =========================================================================
// 1. INICIALIZAR EL MAPA Y CAPAS
// =========================================================================
const map = L.map('map', {
    zoomControl: false
}).setView([-33.4489, -70.6693], 5);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri — Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
    maxZoom: 18
}).addTo(map);

// Crear un pane exclusivo por encima de los polígonos normales (overlayPane tiene zIndex 400)
map.createPane('paneBordesRegiones');
map.getPane('paneBordesRegiones').style.zIndex = 450;
// Crucial: permite que los clics y el hover atraviesen este borde y lleguen a las comunas
map.getPane('paneBordesRegiones').style.pointerEvents = 'none';

// =========================================================================
// 2. CAPAS GEOJSON: REGIONES Y COMUNAS DE CHILE
// =========================================================================
let capaRegiones = null;
let capaComunas = null;
const ZOOM_CORTE = 9; // Nivel de zoom donde cambia de Región a Comuna
let enVuelo = false;
let popupAbierto = false;

// Se dispara automáticamente cuando termina cualquier flyTo, zoom o arrastre
map.on('moveend', function () {
    enVuelo = false;
});
// Se dispara cuando se abre un popup (para evitar cerrar la capa de comunas mientras el popup está abierto)
map.on('popupopen', function () {
    popupAbierto = true;
    capaConPopupAbierto = e.popup._source || null;
});

map.on('popupclose', function () {
    setTimeout(() => {
        popupAbierto = false;
        capaConPopupAbierto = null;
    }, 50);
});



// Estilos base y al pasar el mouse (hover)
const estiloRegion = {
    color: '#2c3e50',
    weight: 2,
    fillColor: '#3498db',
    fillOpacity: 0.15
};

const estiloBordeRegiones = {
    color: '#1a252f',      // Azul oscuro / casi negro para alto contraste
    weight: 3.5,           // Borde más grueso que el de las comunas (weight: 1)
    opacity: 0.9,
    fill: false,           // Sin relleno para no tapar las comunas ni sus colores
    interactive: false,    // No bloquea clics ni tooltips de las comunas
    pane: 'paneBordesRegiones'
};

const estiloComuna = {
    color: '#e74c3c',
    weight: 1,
    fillColor: '#f1c40f',
    fillOpacity: 0.15
};

function resaltarPoligono(e) {

    if (enVuelo || popupAbierto) return;

    const layer = e.target;
    layer.setStyle({
        weight: 3,
        fillOpacity: 0.35
    });
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

// A. Cargar GeoJSON de Regiones (se muestra de inmediato)
fetch('/static/geojson/regiones.geojson')
    .then(res => res.json())
    .then(data => {
        capaRegiones = L.geoJSON(data, {
            style: estiloRegion,
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const nombreRegion = props.Region || 'Región sin nombre';

                layer.bindTooltip(`<b>${nombreRegion}</b>`, { sticky: true });

                layer.on({
                    mouseover: resaltarPoligono,
                    mouseout: (e) => capaRegiones.resetStyle(e.target),
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);

                        if (enVuelo) return;
                        // Al hacer clic en una región, hace zoom hacia ella
                        // Excepción para Valparaíso (evita que Rapa Nui tire el centro al océano)
                        if (props.codregion === 5 || (props.Region && props.Region.includes('Valparaíso'))) {
                            // Coordenadas en el centro continental de la Región de Valparaíso (zona Quillota/Limache)
                            centroRegion = [-32.90, -71.20];
                        } else {
                            // Para el resto de las regiones calcula su centro normal
                            centroRegion = e.target.getBounds().getCenter();
                        }

                        map.flyTo(centroRegion, ZOOM_CORTE, { duration: 1 });
                    }
                });
            }
        });



        if (map.getZoom() < ZOOM_CORTE) {
            capaRegiones.addTo(map);
        }

        capaBordesRegiones = L.geoJSON(data, {
            style: estiloBordeRegiones
        });

        if (map.getZoom() < ZOOM_CORTE) {
            capaRegiones.addTo(map);
        } else {
            capaBordesRegiones.addTo(map);
        }
    })
    .catch(err => console.error("Error cargando regiones.geojson:", err));

// B. Cargar GeoJSON de Comunas (se guarda en memoria y se activa con zoom)
fetch('/static/geojson/comunas.geojson')
    .then(res => res.json())
    .then(data => {
        capaComunas = L.geoJSON(data, {
            style: estiloComuna,
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                // Propiedades exactas de tu GeoJSON
                const comuna = props.Comuna || 'Sin nombre';
                const provincia = props.Provincia || '';
                const region = props.Region || '';

                layer.bindTooltip(`<b>${comuna}</b>`, { sticky: true });
                layer.bindPopup(`
                    <div style="font-family: sans-serif; min-width: 160px;">
                        <h6 style="margin: 0 0 4px 0; font-weight: bold;">${comuna}</h6>
                        <p style="margin: 0; font-size: 0.85rem;"><strong>Provincia:</strong> ${provincia}</p>
                        <p style="margin: 0; font-size: 0.85rem;"><strong>Región:</strong> ${region}</p>
                    </div>
                `);

                layer.on({
                    mouseover: resaltarPoligono,
                    mousemove: (e) => {
                        // Evita que el tooltip sticky reaparezca al mover el cursor con un popup abierto
                        if (popupAbierto || enVuelo) {
                            e.target.closeTooltip();
                        }
                    },
                    mouseout: (e) => capaComunas.resetStyle(e.target),
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);

                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaComunas.resetStyle(e.target);
                        enVuelo = true;

                        const centerComuna = e.target.getBounds().getCenter();
                        const zoomActual = map.getZoom();
                        map.flyTo(centerComuna, zoomActual, { duration: .5 });
                        layer.openPopup();
                    }
                });
            }
        });

        if (map.getZoom() >= ZOOM_CORTE) {
            capaComunas.addTo(map);
        }
    })
    .catch(err => console.error("Error cargando comunas.geojson:", err));

// C. Controlador de cambio automático según nivel de zoom
map.on('zoomend', function () {
    const zoomActual = map.getZoom();

    if (zoomActual >= ZOOM_CORTE) {
        // Oculta la capa interactiva de regiones y activa comunas + bordes regionales gruesos
        if (capaRegiones && map.hasLayer(capaRegiones)) {
            map.removeLayer(capaRegiones);
        }
        if (capaComunas && !map.hasLayer(capaComunas)) {
            map.addLayer(capaComunas);
        }
        if (capaBordesRegiones && !map.hasLayer(capaBordesRegiones)) {
            map.addLayer(capaBordesRegiones);
        }
    } else {
        // Vuelve a la vista general de regiones
        if (capaComunas && map.hasLayer(capaComunas)) {
            map.removeLayer(capaComunas);
        }
        if (capaBordesRegiones && map.hasLayer(capaBordesRegiones)) {
            map.removeLayer(capaBordesRegiones);
        }
        if (capaRegiones && !map.hasLayer(capaRegiones)) {
            map.addLayer(capaRegiones);
        }
    }
});

// =========================================================================
// 4. BUSCADOR DE LUGARES EN CHILE
// =========================================================================
const inputBuscar = document.getElementById('inputBuscar');
let marcadorBusqueda = null;

if (inputBuscar) {
    inputBuscar.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            const lugar = inputBuscar.value.trim();
            if (!lugar) return;

            const url = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=cl&q=${encodeURIComponent(lugar)}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const primerResultado = data[0];
                        const lat = parseFloat(primerResultado.lat);
                        const lon = parseFloat(primerResultado.lon);

                        // Al volar a zoom 12, se activará automáticamente la capa de comunas
                        map.flyTo([lat, lon], 12, { duration: 1.5 });

                        if (marcadorBusqueda) {
                            map.removeLayer(marcadorBusqueda);
                        }

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
}