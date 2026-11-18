// =========================================================================
// 1. INICIALIZAR EL MAPA Y PANES
// =========================================================================
const map = L.map('map', {
    zoomControl: false,
    preferCanvas: true,
}).setView([-33.4489, -70.6693], 5);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri — Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community',
    maxZoom: 18
}).addTo(map);

map.createPane('paneBordesRegiones');
map.getPane('paneBordesRegiones').style.zIndex = 450;
map.getPane('paneBordesRegiones').style.pointerEvents = 'none';

// =========================================================================
// 2. VARIABLES DE ESTADO Y DATOS DESDE DJANGO
// =========================================================================
let capaRegiones = null;
let capaBordesRegiones = null;
let capaComunas = null;
const ZOOM_CORTE = 9;

let enVuelo = false;
let popupAbierto = false;
let capaConPopupAbierto = null;
let capaActivaColor = 'aire'; // 'aire' | 'agua'

const aireComunas = JSON.parse(document.getElementById('aire-comunas-data')?.textContent || '{}');
const aireRegiones = JSON.parse(document.getElementById('aire-regiones-data')?.textContent || '{}');
const aguaComunas = JSON.parse(document.getElementById('agua-comunas-data')?.textContent || '{}');
const aguaRegiones = JSON.parse(document.getElementById('agua-regiones-data')?.textContent || '{}');

function normalizarTexto(texto) {
    if (!texto) return "";
    return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase().replace(/\s+/g, " ");
}

map.on('moveend', function () {
    enVuelo = false;
});

map.on('popupopen', function (e) {
    if (modoReporteActivo) {
        map.closePopup(e.popup);
        return
    }
    popupAbierto = true;
    capaConPopupAbierto = e.popup._source || null;
});

map.on('popupclose', function () {
    setTimeout(() => {
        if (!map._popup) {
            popupAbierto = false;
            capaConPopupAbierto = null;
        }
    }, 50);
});

// =========================================================================
// 3. ESTILOS DINÁMICOS (AIRE O AGUA) E INTERACCIÓN HOVER
// =========================================================================
const estiloBordeRegiones = {
    color: '#1a252f',
    weight: 3.5,
    opacity: 0.9,
    fill: false,
    interactive: false,
    pane: 'paneBordesRegiones'
};

function obtenerEstiloRegion(feature) {
    const regNorm = normalizarTexto(feature.properties.Region);
    const fuente = capaActivaColor === 'agua' ? aguaRegiones[regNorm] : aireRegiones[regNorm];
    return {
        color: '#2c3e50',
        weight: 2,
        fillColor: fuente ? fuente.color : '#95a5a6',
        fillOpacity: fuente ? 0.35 : 0.15
    };
}

function obtenerEstiloComuna(feature) {
    const comNorm = normalizarTexto(feature.properties.Comuna);
    const fuente = capaActivaColor === 'agua' ? aguaComunas[comNorm] : aireComunas[comNorm];
    return {
        color: '#34495e',
        weight: 1,
        fillColor: fuente ? fuente.color : '#bdc3c7',
        fillOpacity: fuente ? 0.35 : 0.12
    };
}

function resaltarPoligono(e) {
    const layer = e.target;
    if (enVuelo || popupAbierto || layer === capaConPopupAbierto) {
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
// 4. SELECTOR FLOTANTE DE CAPA VISUAL (AIRE VS AGUA)
// =========================================================================
const selectorCapa = L.control({ position: 'topright' });
selectorCapa.onAdd = function () {
    const div = L.DomUtil.create('div', 'layer-switcher-card');
    div.innerHTML = `
        <div class="layer-switcher-title">COLOREAR MAPA POR:</div>
        <div class="layer-switcher-group" role="group">
            <button type="button" id="btnCapaAire" class="layer-switcher-btn active">Aire (SINCA)</button>
            <button type="button" id="btnCapaAgua" class="layer-switcher-btn">Agua (SISS)</button>
        </div>
    `;
    L.DomEvent.disableClickPropagation(div);
    return div;
};
selectorCapa.addTo(map);

document.addEventListener('click', function (e) {
    if (e.target.id === 'btnCapaAire' || e.target.id === 'btnCapaAgua') {
        capaActivaColor = e.target.id === 'btnCapaAgua' ? 'agua' : 'aire';

        document.getElementById('btnCapaAire').classList.toggle('active', capaActivaColor === 'aire');
        document.getElementById('btnCapaAgua').classList.toggle('active', capaActivaColor === 'agua');

        if (capaRegiones) capaRegiones.setStyle(obtenerEstiloRegion);
        if (capaComunas) capaComunas.setStyle(obtenerEstiloComuna);
    }
});

// =========================================================================
// 5. CAPA GEOJSON: REGIONES DE CHILE
// =========================================================================
fetch('/static/geojson/regiones.geojson')
    .then(res => res.json())
    .then(data => {
        capaRegiones = L.geoJSON(data, {
            style: obtenerEstiloRegion,
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const nombreRegion = props.Region || 'Región sin nombre';
                const regNorm = normalizarTexto(nombreRegion);
                const aire = aireRegiones[regNorm];
                const agua = aguaRegiones[regNorm];

                layer.bindTooltip(`<b>${nombreRegion}</b>`, { sticky: true });

                const htmlAire = aire
                    ? `<span style="background: ${aire.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${aire.estado}
                       </span>
                       <span style="font-size: 0.85rem; margin-left: 5px;">
                           <strong>${aire.promedio} ${aire.unidad}</strong> (${aire.parametro})
                       </span>
                       <br><small style="color: #666;">Promedio de ${aire.total_mediciones} estación(es)</small>`
                    : `<span style="color: gray; font-size: 0.82rem;">Sin estaciones SINCA registradas</span>`;

                const htmlAgua = agua
                    ? `<span style="background: ${agua.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${agua.estado}
                       </span>
                       ${agua.promedio !== null
                        ? `<span style="font-size: 0.85rem; margin-left: 5px;"><strong>pH ${agua.promedio}</strong> (NCh 409: ${agua.limite})</span>`
                        : ''}
                       <br><small style="color: #666;">${agua.total_servicios} servicio(s) SISS (${agua.periodo})</small>`
                    : `<span style="color: gray; font-size: 0.82rem;">Sin registros SISS disponibles</span>`;

                layer.bindPopup(`
                    <div style="font-family: sans-serif; min-width: 230px;">
                        <h6 style="margin: 0 0 8px 0; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 4px;">
                            ${nombreRegion}
                        </h6>
                        <div style="margin-bottom: 8px;">
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                CALIDAD DEL AIRE (SINCA)
                            </small>
                            ${htmlAire}
                        </div>
                        <div style="border-top: 1px solid #eee; padding-top: 6px;">
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                AGUA POTABLE (SISS)
                            </small>
                            ${htmlAgua}
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

                        if (modoReporteActivo) {
                            layer.closePopup();
                            moverPinUbicacion(e.latlng);
                            return;
                        }
                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaRegiones.resetStyle(e.target);
                        capaConPopupAbierto = layer;
                        layer.openPopup(e.latlng);
                    },
                    dblclick: (e) => {
                        L.DomEvent.stopPropagation(e);

                        if (modoReporteActivo) {
                            layer.closePopup();
                            moverPinUbicacion(e.latlng);
                        }
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
// 6. CAPA GEOJSON: COMUNAS DE CHILE
// =========================================================================
fetch('/static/geojson/comunas.geojson')
    .then(res => res.json())
    .then(data => {
        capaComunas = L.geoJSON(data, {
            style: obtenerEstiloComuna,
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const comuna = props.Comuna || 'Sin nombre';
                const region = props.Region || '';
                const comNorm = normalizarTexto(comuna);
                const aire = aireComunas[comNorm];
                const agua = aguaComunas[comNorm];

                layer.bindTooltip(`<b>${comuna}</b>`, { sticky: true });

                const htmlAire = aire
                    ? `<span style="background: ${aire.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${aire.estado}
                       </span>
                       <span style="font-size: 0.85rem; margin-left: 5px;">
                           <strong>${aire.valor} ${aire.unidad}</strong> (${aire.parametro})
                       </span>
                       <br><small style="color: #666;">Estación: ${aire.estaciones.join(', ')}</small>
                       ${aire.fecha ? `<br><small style="color: gray;">Actualizado: ${aire.fecha}</small>` : ''}`
                    : `<span style="color: gray; font-size: 0.82rem;">Sin estación SINCA en esta comuna</span>`;

                const htmlAgua = agua
                    ? `<span style="background: ${agua.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                           ${agua.estado}
                       </span>
                       ${agua.valor !== null
                        ? `<span style="font-size: 0.85rem; margin-left: 5px;"><strong>pH ${agua.valor}</strong> (Límite: ${agua.limite})</span>`
                        : ''}
                       <br><small style="color: #666;">Servicio: ${agua.servicios.join(', ')}</small>
                       <br><small style="color: gray;">Periodo SISS: ${agua.periodo}</small>`
                    : `<span style="color: gray; font-size: 0.82rem;">Sin servicio SISS registrado en esta comuna</span>`;

                layer.bindPopup(`
                    <div style="font-family: sans-serif; min-width: 220px;">
                        <h6 style="margin: 0 0 2px 0; font-weight: bold;">${comuna}</h6>
                        <small style="color: gray; display: block; margin-bottom: 8px; border-bottom: 1px solid #ddd; padding-bottom: 4px;">
                            ${region}
                        </small>
                        <div style="margin-bottom: 8px;">
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                CALIDAD DEL AIRE (SINCA)
                            </small>
                            ${htmlAire}
                        </div>
                        <div style="border-top: 1px solid #eee; padding-top: 6px;">
                            <small style="color: #555; font-weight: bold; display: block; margin-bottom: 2px;">
                                AGUA POTABLE (SISS)
                            </small>
                            ${htmlAgua}
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

                        if (modoReporteActivo) {
                            layer.closePopup();
                            moverPinUbicacion(e.latlng);
                            return;
                        }
                        if (enVuelo) return;

                        e.target.closeTooltip();
                        capaComunas.resetStyle(e.target);
                        enVuelo = true;
                        capaConPopupAbierto = layer;

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
// 7. CONTROLADOR DE CAMBIO AUTOMÁTICO SEGÚN NIVEL DE ZOOM
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
        if (capaReportes && !map.hasLayer(capaReportes)) {
            map.addLayer(capaReportes);
        }
    } else {
        if (capaComunas && map.hasLayer(capaComunas)) {
            map.removeLayer(capaComunas);
        }
        if (capaBordesRegiones && map.hasLayer(capaBordesRegiones)) {
            map.removeLayer(capaBordesRegiones);
        }
        if (capaReportes && map.hasLayer(capaReportes)) {
            map.removeLayer(capaReportes);
        }
        if (capaRegiones && !map.hasLayer(capaRegiones)) {
            map.addLayer(capaRegiones);
        }
    }
});

// =========================================================================
// 8. BUSCADOR DE LUGARES EN CHILE (REGIONES Y COMUNAS CON POPUP AMBIENTAL)
// =========================================================================
const inputBuscar = document.getElementById('inputBuscar');
let marcadorBusqueda = null;

function _puntoEnAnillo(lon, lat, anillo) {
    let dentro = false;
    for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
        const xi = anillo[i][0], yi = anillo[i][1];
        const xj = anillo[j][0], yj = anillo[j][1];
        const intersecta = ((yi > lat) !== (yj > lat)) &&
            (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi);
        if (intersecta) dentro = !dentro;
    }
    return dentro;
}

function _puntoEnPoligono(lon, lat, poligono) {
    if (!poligono || poligono.length === 0 || !_puntoEnAnillo(lon, lat, poligono[0])) {
        return false;
    }
    for (let i = 1; i < poligono.length; i++) {
        if (_puntoEnAnillo(lon, lat, poligono[i])) return false;
    }
    return true;
}

function obtenerCentroRegion(layer) {
    const props = layer.feature?.properties || {};
    if (props.codregion === 5 || (props.Region && props.Region.includes('Valparaíso'))) {
        return L.latLng(-32.90, -71.20);
    }
    return layer.getBounds().getCenter();
}

function buscarCapaRegion(textoBusqueda) {
    if (!capaRegiones) return null;

    const textoNorm = normalizarTexto(textoBusqueda);
    const q = textoNorm
        .replace(/^REGION\s+(DE\s+LA\s+|DE\s+LOS\s+|DEL\s+|DE\s+)?/, '')
        .trim();
    if (!q) return null;

    // Nombres compartidos por comuna y región: solo se toman como región si incluye "region"
    const nombresAmbiguos = new Set(['ARICA', 'ANTOFAGASTA', 'COQUIMBO', 'VALPARAISO']);
    if (nombresAmbiguos.has(q) && !textoNorm.includes('REGION')) {
        return null;
    }

    let coincidencia = null;
    capaRegiones.eachLayer(function (layer) {
        if (coincidencia) return;
        const regRaw = normalizarTexto(layer.feature?.properties?.Region || '');
        const regCorta = regRaw
            .replace(/^REGION\s+(DE\s+LA\s+|DE\s+LOS\s+|DEL\s+|DE\s+)?/, '')
            .trim();

        if (
            regRaw === textoNorm ||
            regCorta === q ||
            (q.length >= 4 && regCorta.includes(q)) ||
            (q === 'RM' && regRaw.includes('METROPOLITANA'))
        ) {
            coincidencia = layer;
        }
    });

    return coincidencia;
}

function buscarCapaComuna(lat, lon, nombreLugar = '') {
    if (!capaComunas) return null;

    let capaPorCoordenada = null;
    let capaPorNombre = null;
    const nombreNorm = normalizarTexto(nombreLugar.split(',')[0]);

    capaComunas.eachLayer(function (layer) {
        const geom = layer.feature?.geometry;
        const comNorm = normalizarTexto(layer.feature?.properties?.Comuna || '');

        if (!capaPorNombre && nombreNorm && comNorm === nombreNorm) {
            capaPorNombre = layer;
        }

        if (!capaPorCoordenada && geom) {
            if (geom.type === 'Polygon' && _puntoEnPoligono(lon, lat, geom.coordinates)) {
                capaPorCoordenada = layer;
            } else if (geom.type === 'MultiPolygon') {
                for (const poly of geom.coordinates) {
                    if (_puntoEnPoligono(lon, lat, poly)) {
                        capaPorCoordenada = layer;
                        break;
                    }
                }
            }
        }
    });

    return capaPorCoordenada || capaPorNombre;
}

function abrirPopupBusqueda(capaObjetivo, latlng) {
    if (marcadorBusqueda) {
        map.removeLayer(marcadorBusqueda);
        marcadorBusqueda = null;
    }

    marcadorBusqueda = L.marker(latlng).addTo(map);

    if (capaObjetivo && capaObjetivo.getPopup()) {
        const contenidoAmbiental = capaObjetivo.getPopup().getContent();
        marcadorBusqueda.bindPopup(contenidoAmbiental);
        capaConPopupAbierto = capaObjetivo;
        capaObjetivo.openPopup(latlng);
    }
}

if (inputBuscar) {
    inputBuscar.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const lugar = inputBuscar.value.trim();
            if (!lugar) return;

            // 1. Verificar primero si el usuario escribió una Región
            const capaRegionDirecta = buscarCapaRegion(lugar);
            if (capaRegionDirecta) {
                const centroRegion = obtenerCentroRegion(capaRegionDirecta);
                enVuelo = true;
                map.flyTo(centroRegion, 7, { duration: 1.4 });

                map.once('moveend', function () {
                    abrirPopupBusqueda(capaRegionDirecta, centroRegion);
                });
                return;
            }

            // 2. Si no es región, buscar comuna/ciudad/sector con Nominatim
            const url = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=cl&q=${encodeURIComponent(lugar)}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const primerResultado = data[0];
                        const lat = parseFloat(primerResultado.lat);
                        const lon = parseFloat(primerResultado.lon);

                        // Respaldo si Nominatim clasifica el resultado como región ('state')
                        if (primerResultado.addresstype === 'state') {
                            const capaRegNom = buscarCapaRegion(primerResultado.name || lugar);
                            if (capaRegNom) {
                                const centroReg = obtenerCentroRegion(capaRegNom);
                                enVuelo = true;
                                map.flyTo(centroReg, 7, { duration: 1.4 });
                                map.once('moveend', function () {
                                    abrirPopupBusqueda(capaRegNom, centroReg);
                                });
                                return;
                            }
                        }

                        enVuelo = true;
                        map.flyTo([lat, lon], 12, { duration: 1.5 });

                        map.once('moveend', function () {
                            const capaComuna = buscarCapaComuna(lat, lon, primerResultado.display_name);

                            if (capaComuna && capaComuna.getPopup()) {
                                abrirPopupBusqueda(capaComuna, [lat, lon]);
                            } else {
                                if (marcadorBusqueda) map.removeLayer(marcadorBusqueda);
                                marcadorBusqueda = L.marker([lat, lon])
                                    .addTo(map)
                                    .bindPopup(`<b>${primerResultado.display_name}</b><br><small style="color: gray;">Sin datos comunales en este punto</small>`)
                                    .openPopup();
                            }
                        });
                    } else {
                        alert("No encontramos ese lugar en Chile. Intenta con otra comuna, región o ciudad.");
                    }
                })
                .catch(err => {
                    console.error("Error al buscar:", err);
                    alert("Hubo un problema al buscar la ubicación.");
                });
        }
    });
}

// ===============================================================
// 9. SISTEMA DE REPORTES CIUDADANOS (MODO REPORTE, PINES Y VOTOS
// ===============================================================
const isAuthenticated = JSON.parse(document.getElementById('user-auth-data')?.textContent || 'false');

const CATALOGO_REPORTES = {
    agua: {
        nombre: 'Agua',
        color: '#0d6efd',
        svgPin: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
        etiquetaEscala: '3. Nivel de gravedad (1 al 3)',
        problemas: [
            'Zona de desperdicios líquidos',
            'Agua contaminada por químicos',
            'Agua con residuos sólidos / contaminación humana',
        ],
    },
    aire: {
        nombre: 'Aire',
        color: '#6f42c1',
        svgPin: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M14.5 17c0 1.65-1.35 3-3 3s-3-1.35-3-3h2c0 .55.45 1 1 1s1-.45 1-1-.45-1-1-1H2v-2h9.5c1.65 0 3 1.35 3 3zM19 6.5C19 4.57 17.43 3 15.5 3S12 4.57 12 6.5h2c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5S16.33 8 15.5 8H2v2h13.5c1.93 0 3.5-1.57 3.5-3.5zm-.5 4.5H2v2h16.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5v2c1.93 0 3.5-1.57 3.5-3.5S20.43 11 18.5 11z"/></svg>',
        etiquetaEscala: '3. Nivel de gravedad (1 al 3)',
        problemas: [
            'Aire pesado / humo',
            'Mal olor',
        ],
    },
    residuos: {
        nombre: 'Residuos Sólidos',
        color: '#fd7e14',
        svgPin: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>',
        etiquetaEscala: '3. Cantidad de residuos (1 al 3)',
        problemas: [
            'Microbasural / acumulación de basura',
            'Escombros o residuos voluminosos',
            'Contenedor / punto de acopio desbordado',
        ],
    },
};

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

// Controladores puros de Modales
function abrirModal(modalEl) {
    if (modalEl) modalEl.classList.add('open');
}

function cerrarModal(modalEl) {
    if (modalEl) modalEl.classList.remove('open');
}

document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
        cerrarModal(document.getElementById(btn.dataset.closeModal));
    });
});

document.querySelectorAll('.rep-modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cerrarModal(overlay);
    });
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.rep-modal-overlay.open').forEach(cerrarModal);
    }
});

// Estado global de reportes
let modoReporteActivo = false;
let pinUbicacionReporte = null;
let seleccionReporte = { categoria: null, problema: null, gravedad: null, lat: null, lon: null };
let reporteActualModal = null;
const capaReportes = L.layerGroup();
const marcadoresReportesPorId = new Map();

const modalLoginEl = document.getElementById('modalLoginRequerido');
const modalCrearEl = document.getElementById('modalCrearReporte');
const modalDetalleEl = document.getElementById('modalDetalleReporte');

const bannerModoReporte = document.getElementById('banner-modo-reporte');
const btnAbrirReporte = document.getElementById('btn-abrir-reporte');

const modalErrorUbicacionEl = document.getElementById('modalErrorUbicacion');
let ultimaUbicacionValida = null;

if (map.getZoom() >= ZOOM_CORTE) {
    capaReportes.addTo(map);
}

function estaEnChile(lat, lon) {
    const capas = [capaRegiones, capaComunas].filter(Boolean);
    if (capas.length === 0) {
        // Respaldo si los GeoJSON aún no terminan de cargar
        return lat >= -56.5 && lat <= -17.4 && lon >= -109.5 && lon <= -66.3;
    }

    for (const capa of capas) {
        let dentro = false;
        capa.eachLayer(function (layer) {
            if (dentro) return;
            const geom = layer.feature?.geometry;
            if (!geom) return;

            if (geom.type === 'Polygon' && _puntoEnPoligono(lon, lat, geom.coordinates)) {
                dentro = true;
            } else if (geom.type === 'MultiPolygon') {
                for (const poly of geom.coordinates) {
                    if (_puntoEnPoligono(lon, lat, poly)) {
                        dentro = true;
                        break;
                    }
                }
            }
        });
        if (dentro) return true;
    }
    return false;
}

function moverPinUbicacion(latlng) {
    if (!estaEnChile(latlng.lat, latlng.lng)) {
        // Devuelve el pin a la última posición válida dentro de Chile sin salir del Modo Reporte
        if (pinUbicacionReporte && ultimaUbicacionValida) {
            pinUbicacionReporte.setLatLng(ultimaUbicacionValida);
        }
        abrirModal(modalErrorUbicacionEl);
        return false;
    }

    ultimaUbicacionValida = latlng;
    seleccionReporte.lat = latlng.lat;
    seleccionReporte.lon = latlng.lng;
    if (pinUbicacionReporte) {
        pinUbicacionReporte.setLatLng(latlng);
    }
    return true;
}

function activarModoReporte() {
    map.closePopup();
    popupAbierto = false;
    capaConPopupAbierto = null;

    modoReporteActivo = true;
    bannerModoReporte.classList.remove('hidden');
    btnAbrirReporte.classList.add('hidden');

    const centroActual = map.getCenter();
    const centroEsValido = estaEnChile(centroActual.lat, centroActual.lng);

    ultimaUbicacionValida = centroEsValido ? centroActual : null;
    seleccionReporte = {
        categoria: null,
        problema: null,
        gravedad: null,
        lat: centroEsValido ? centroActual.lat : null,
        lon: centroEsValido ? centroActual.lng : null,
    };

    if (pinUbicacionReporte) map.removeLayer(pinUbicacionReporte);
    pinUbicacionReporte = L.marker(centroActual, {
        draggable: true,
        zIndexOffset: 1000,
    })
        .addTo(map)
        .bindTooltip('Arrástrame o haz clic en el mapa', {
            permanent: true,
            direction: 'top',
            interactive: false,
        });

    pinUbicacionReporte.on('dragend', function (e) {
        moverPinUbicacion(e.target.getLatLng());
    });

    if (!centroEsValido) {
        abrirModal(modalErrorUbicacionEl);
    }
}

function desactivarModoReporte() {
    modoReporteActivo = false;
    bannerModoReporte.classList.add('hidden');
    btnAbrirReporte.classList.remove('hidden');
    if (pinUbicacionReporte) {
        map.removeLayer(pinUbicacionReporte);
        pinUbicacionReporte = null;
    }
}

function centrarEnGPS() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
        function (pos) {
            if (!modoReporteActivo) return;
            const latlng = L.latLng(pos.coords.latitude, pos.coords.longitude);
            map.flyTo(latlng, Math.max(map.getZoom(), 15), { duration: 1.0 });
            moverPinUbicacion(latlng);
        },
        function () { },
        { enableHighAccuracy: true, timeout: 5000 }
    );
}

map.on('click', function (e) {
    if (modoReporteActivo) {
        moverPinUbicacion(e.latlng);
    }
});

if (btnAbrirReporte) {
    btnAbrirReporte.addEventListener('click', function () {
        if (!isAuthenticated) {
            abrirModal(modalLoginEl);
            return;
        }
        activarModoReporte();
    });
}

document.getElementById('btn-gps-reporte')?.addEventListener('click', centrarEnGPS);
document.getElementById('btn-cancelar-reporte')?.addEventListener('click', desactivarModoReporte);

document.getElementById('btn-confirmar-ubicacion')?.addEventListener('click', function () {
    resetearFormularioReporte();
    abrirModal(modalCrearEl);
});

// Lógica interna del Modal de Creación (Waze)
function resetearFormularioReporte() {
    seleccionReporte.categoria = null;
    seleccionReporte.problema = null;
    seleccionReporte.gravedad = null;

    document.querySelectorAll('.rep-cat-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.rep-grav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('bloque-problema').classList.add('hidden');
    document.getElementById('bloque-gravedad').classList.add('hidden');
    document.getElementById('btn-enviar-reporte').disabled = true;
}

function validarFormularioReporte() {
    const listo = Boolean(seleccionReporte.categoria && seleccionReporte.problema && seleccionReporte.gravedad);
    document.getElementById('btn-enviar-reporte').disabled = !listo;
}

document.querySelectorAll('.rep-cat-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.rep-cat-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const cat = this.dataset.cat;
        seleccionReporte.categoria = cat;
        seleccionReporte.problema = null;
        seleccionReporte.gravedad = null;

        const config = CATALOGO_REPORTES[cat];
        const listaProblemas = document.getElementById('lista-problemas');
        listaProblemas.innerHTML = '';

        config.problemas.forEach(prob => {
            const itemBtn = document.createElement('button');
            itemBtn.type = 'button';
            itemBtn.className = 'rep-prob-btn';
            itemBtn.textContent = prob;
            itemBtn.addEventListener('click', function () {
                listaProblemas.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                seleccionReporte.problema = prob;
                document.getElementById('titulo-gravedad').textContent = config.etiquetaEscala;
                document.getElementById('bloque-gravedad').classList.remove('hidden');
                validarFormularioReporte();
            });
            listaProblemas.appendChild(itemBtn);
        });

        document.getElementById('bloque-problema').classList.remove('hidden');
        document.getElementById('bloque-gravedad').classList.add('hidden');
        document.querySelectorAll('.rep-grav-btn').forEach(b => b.classList.remove('active'));
        validarFormularioReporte();
    });
});

document.querySelectorAll('.rep-grav-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.rep-grav-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        seleccionReporte.gravedad = parseInt(this.dataset.grav, 10);
        validarFormularioReporte();
    });
});

document.getElementById('btn-enviar-reporte')?.addEventListener('click', function () {
    const btnEnviar = this;
    btnEnviar.disabled = true;

    fetch('/reportes/api/crear/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(seleccionReporte),
    })
        .then(res => res.json())
        .then(data => {
            if (data.ok && data.reporte) {
                dibujarPinReporte(data.reporte);
                cerrarModal(modalCrearEl);
                desactivarModoReporte();
            } else {
                alert(data.error || 'No se pudo guardar el reporte.');
                btnEnviar.disabled = false;
            }
        })
        .catch(() => {
            alert('Error de conexión al enviar el reporte.');
            btnEnviar.disabled = false;
        });
});

// Dibujo de pines y Modal de Votación
function dibujarPinReporte(rep) {
    const config = CATALOGO_REPORTES[rep.categoria] || CATALOGO_REPORTES.residuos;
    const iconoHtml = L.divIcon({
        className: '',
        html: `<div class="report-pin-badge" style="background:${config.color};">
                   ${config.svgPin}
                   <span class="report-pin-level">${rep.gravedad}</span>
               </div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
    });

    const marker = L.marker([rep.lat, rep.lon], { icon: iconoHtml }).addTo(capaReportes);
    marker.reporteData = rep;
    marker.on('click', function (e) {
        L.DomEvent.stopPropagation(e);
        if (modoReporteActivo) return;
        abrirModalDetalleReporte(marker.reporteData);
    });

    marcadoresReportesPorId.set(rep.id, marker);
}

function actualizarBotonesVoto(rep) {
    const btnLike = document.getElementById('btn-voto-like');
    const btnDislike = document.getElementById('btn-voto-dislike');

    document.getElementById('det-likes').textContent = rep.likes;
    document.getElementById('det-dislikes').textContent = rep.dislikes;

    btnLike.classList.toggle('active-like', rep.mi_voto === 1);
    btnDislike.classList.toggle('active-dislike', rep.mi_voto === -1);
}

function abrirModalDetalleReporte(rep) {
    reporteActualModal = rep;
    const config = CATALOGO_REPORTES[rep.categoria] || CATALOGO_REPORTES.residuos;

    const badgeCat = document.getElementById('det-badge-cat');
    badgeCat.textContent = rep.categoria_display;
    badgeCat.style.backgroundColor = config.color;

    document.getElementById('det-badge-grav').textContent = `Nivel ${rep.gravedad}/3`;
    document.getElementById('det-problema').textContent = rep.problema;
    document.getElementById('det-usuario').textContent = rep.usuario;
    document.getElementById('det-fecha').textContent = rep.fecha;

    actualizarBotonesVoto(rep);
    abrirModal(modalDetalleEl);
}

function enviarVoto(valor) {
    if (!reporteActualModal) return;
    if (!isAuthenticated) {
        cerrarModal(modalDetalleEl);
        abrirModal(modalLoginEl);
        return;
    }

    fetch(`/reportes/api/${reporteActualModal.id}/votar/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ valor }),
    })
        .then(res => {
            if (res.status === 401) {
                cerrarModal(modalDetalleEl);
                abrirModal(modalLoginEl);
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (!data || !data.ok) return;
            reporteActualModal.likes = data.likes;
            reporteActualModal.dislikes = data.dislikes;
            reporteActualModal.mi_voto = data.mi_voto;
            actualizarBotonesVoto(reporteActualModal);
        });
}

document.getElementById('btn-voto-like')?.addEventListener('click', () => enviarVoto(1));
document.getElementById('btn-voto-dislike')?.addEventListener('click', () => enviarVoto(-1));

// Cargar reportes existentes al iniciar
fetch('/reportes/api/')
    .then(res => res.json())
    .then(data => {
        (data.reportes || []).forEach(dibujarPinReporte);
    })
    .catch(err => console.error('Error cargando reportes ciudadanos:', err));