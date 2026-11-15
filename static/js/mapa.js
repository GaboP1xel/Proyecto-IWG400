// =========================================================================
// 1. INICIALIZAR EL MAPA Y PANES
// =========================================================================
const map = L.map('map', {
    zoomControl: false
}).setView([-33.4489, -70.6693], 5);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri — Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
    maxZoom: 18
}).addTo(map);

// Pane exclusivo por encima de los polígonos normales (overlayPane tiene zIndex 400)
map.createPane('paneBordesRegiones');
map.getPane('paneBordesRegiones').style.zIndex = 450;
// Permite que los clics y el hover atraviesen este borde y lleguen a las comunas
map.getPane('paneBordesRegiones').style.pointerEvents = 'none';

// =========================================================================
// 2. VARIABLES DE ESTADO Y DATOS DESDE DJANGO
// =========================================================================
let capaRegiones = null;
let capaBordesRegiones = null;
let capaComunas = null;
const ZOOM_CORTE = 9; // Nivel de zoom donde cambia de Región a Comuna

let enVuelo = false;
let popupAbierto = false;

const aireComunas = JSON.parse(document.getElementById('aire-comunas-data')?.textContent || '{}');
const aireRegiones = JSON.parse(document.getElementById('aire-regiones-data')?.textContent || '{}');

function normalizarTexto(texto) {
    if (!texto) return "";
    return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase().replace(/\s+/g, " ");
}

// Eventos globales de movimiento y popups
map.on('moveend', function () {
    enVuelo = false;
});

map.on('popupopen', function (e) {
    popupAbierto = true;
});

map.on('popupclose', function () {
    setTimeout(() => {
        if (!map._popup) {
            popupAbierto = false;
        }
    }, 50);
});

// =========================================================================
// 3. ESTILOS E INTERACCIÓN HOVER
// =========================================================================
const estiloBordeRegiones = {
    color: '#1a252f',
    weight: 3.5,
    opacity: 0.9,
    fill: false,
    interactive: false,
    pane: 'paneBordesRegiones'
};

function resaltarPoligono(e) {
    const layer = e.target;

    if (enVuelo || popupAbierto) {
        layer.closeTooltip();
        return;
    }

    layer.setStyle({
        weight: 3,
        fillOpacity: 0.45
    });
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

// =========================================================================
// 4. CAPA GEOJSON: REGIONES DE CHILE
// =========================================================================
fetch('/static/geojson/regiones.geojson')
    .then(res => res.json())
    .then(data => {
        capaRegiones = L.geoJSON(data, {
            style: function (feature) {
                const regNorm = normalizarTexto(feature.properties.Region);
                const aire = aireRegiones[regNorm];
                return {
                    color: '#2c3e50',
                    weight: 2,
                    fillColor: aire ? aire.color : '#95a5a6',
                    fillOpacity: aire ? 0.35 : 0.15
                };
            },
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const nombreRegion = props.Region || 'Región sin nombre';
                const regNorm = normalizarTexto(nombreRegion);
                const aire = aireRegiones[regNorm];

                layer.bindTooltip(`<b>${nombreRegion}</b>`, { sticky: true });

                let htmlAire = aire
                    ? `<span style="background: ${aire.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${aire.estado}
                       </span>
                       <span style="font-size: 0.85rem; margin-left: 5px;">
                           <strong>${aire.promedio} ${aire.unidad}</strong> (${aire.parametro})
                       </span>
                       <br><small style="color: #666;">Promedio de ${aire.total_mediciones} estación(es)</small>`
                    : `<span style="color: gray; font-size: 0.85rem;">Sin estaciones SINCA registradas</span>`;

                layer.bindPopup(`
                    <div style="font-family: sans-serif; min-width: 210px;">
                        <h6 style="margin: 0 0 8px 0; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 4px;">
                            ${nombreRegion}
                        </h6>
                        <div style="margin-bottom: 6px;">
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                CALIDAD DEL AIRE (Promedio Regional)
                            </small>
                            ${htmlAire}
                        </div>
                        <small style="display: block; margin-top: 8px; color: #0d6efd;">
                            <i>Doble clic o acerca el mapa para ver comunas</i>
                        </small>
                    </div>
                `);

                layer.on({
                    mouseover: resaltarPoligono,
                    mousemove: (e) => {
                        if (popupAbierto || enVuelo) e.target.closeTooltip();
                    },
                    mouseout: (e) => capaRegiones.resetStyle(e.target),
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);
                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaRegiones.resetStyle(e.target);
                        layer.openPopup(e.latlng);
                    },
                    dblclick: (e) => {
                        L.DomEvent.stopPropagation(e);
                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaRegiones.resetStyle(e.target);
                        enVuelo = true;

                        let centroRegion = (props.codregion === 5 || (props.Region && props.Region.includes('Valparaíso')))
                            ? [-32.90, -71.20]
                            : e.target.getBounds().getCenter();

                        map.flyTo(centroRegion, ZOOM_CORTE, { duration: 1.2 });
                    }
                });
            }
        });

        // Capa persistente de bordes regionales gruesos para vista de comunas
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

// =========================================================================
// 5. CAPA GEOJSON: COMUNAS DE CHILE
// =========================================================================
fetch('/static/geojson/comunas.geojson')
    .then(res => res.json())
    .then(data => {
        capaComunas = L.geoJSON(data, {
            style: function (feature) {
                const comNorm = normalizarTexto(feature.properties.Comuna);
                const aire = aireComunas[comNorm];
                return {
                    color: '#34495e',
                    weight: 1,
                    fillColor: aire ? aire.color : '#bdc3c7',
                    fillOpacity: aire ? 0.35 : 0.12
                };
            },
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const comuna = props.Comuna || 'Sin nombre';
                const region = props.Region || '';
                const comNorm = normalizarTexto(comuna);
                const aire = aireComunas[comNorm];

                layer.bindTooltip(`<b>${comuna}</b>`, { sticky: true });

                let htmlAire = aire
                    ? `<span style="background: ${aire.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${aire.estado}
                       </span>
                       <span style="font-size: 0.85rem; margin-left: 5px;">
                           <strong>${aire.valor} ${aire.unidad}</strong> (${aire.parametro})
                       </span>
                       <br><small style="color: #666;">Estación: ${aire.estaciones.join(', ')}</small>
                       ${aire.fecha ? `<br><small style="color: gray;">Actualizado: ${aire.fecha}</small>` : ''}`
                    : `<span style="color: gray; font-size: 0.85rem;">Sin estación SINCA en esta comuna</span>`;

                layer.bindPopup(`
                    <div style="font-family: sans-serif; min-width: 200px;">
                        <h6 style="margin: 0 0 2px 0; font-weight: bold;">${comuna}</h6>
                        <small style="color: gray; display: block; margin-bottom: 8px;">${region}</small>
                        <div>
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                CALIDAD DEL AIRE (SINCA)
                            </small>
                            ${htmlAire}
                        </div>
                    </div>
                `);

                layer.on({
                    mouseover: resaltarPoligono,
                    mousemove: (e) => {
                        if (popupAbierto || enVuelo) e.target.closeTooltip();
                    },
                    mouseout: (e) => capaComunas.resetStyle(e.target),
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);
                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaComunas.resetStyle(e.target);
                        enVuelo = true;

                        const centroComuna = e.target.getBounds().getCenter();
                        const zoomActual = map.getZoom();

                        map.flyTo(centroComuna, zoomActual, { duration: 1.0 });
                        layer.openPopup(centroComuna);
                    }
                });
            }
        });

        if (map.getZoom() >= ZOOM_CORTE) {
            capaComunas.addTo(map);
        }
    })
    .catch(err => console.error("Error cargando comunas.geojson:", err));

// =========================================================================
// 6. CONTROLADOR DE CAMBIO AUTOMÁTICO SEGÚN NIVEL DE ZOOM
// =========================================================================
map.on('zoomend', function () {
    const zoomActual = map.getZoom();

    if (zoomActual >= ZOOM_CORTE) {
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
// 7. BUSCADOR DE LUGARES EN CHILE
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

                        enVuelo = true;
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