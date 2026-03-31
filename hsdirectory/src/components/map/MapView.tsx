'use client';

import { useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapLocation {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    serviceName?: string;
    serviceId?: string;
}

interface MapViewProps {
    locations: MapLocation[];
    /** ID of the currently highlighted service (e.g. from card hover). */
    highlightedId?: string | null;
}

/** Pin dimensions — default and highlighted. */
const PIN_W = 26;
const PIN_H = 36;
const PIN_HL_W = 32;
const PIN_HL_H = 44;

/**
 * Build an SVG teardrop pin as a data URI.
 * The pin tip sits at the bottom-center so the anchor lines up with coords.
 */
function pinSvg(fill: string, stroke: string, w: number, h: number): string {
    // Bulb radius is ~40% of width, teardrop tapers to bottom point
    const r = w * 0.4;
    const cx = w / 2;
    const bulbTop = r + 2; // slight padding from top
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
      <filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-opacity="0.3"/></filter>
      <path d="M${cx},${h - 1} C${cx - r * 0.15},${h * 0.62} ${cx - r - 2},${bulbTop + r * 0.6} ${cx - r - 2},${bulbTop}
               A${r + 2},${r + 2} 0 1,1 ${cx + r + 2},${bulbTop}
               C${cx + r + 2},${bulbTop + r * 0.6} ${cx + r * 0.15},${h * 0.62} ${cx},${h - 1}Z"
            fill="${fill}" stroke="${stroke}" stroke-width="1.5" filter="url(#s)"/>
      <circle cx="${cx}" cy="${bulbTop}" r="${r * 0.4}" fill="white" opacity="0.5"/>
    </svg>`;
    return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

/** Default and highlighted pin style strings. */
const PIN_DEFAULT = `
    width: ${PIN_W}px; height: ${PIN_H}px;
    background: url("${pinSvg('#8F2D24', '#6b1f18', PIN_W, PIN_H)}") no-repeat center/contain;
    cursor: pointer;
    transition: all 0.15s ease;
    z-index: 1;
`;
const PIN_HIGHLIGHTED = `
    width: ${PIN_HL_W}px; height: ${PIN_HL_H}px;
    background: url("${pinSvg('#f7cf56', '#c9a530', PIN_HL_W, PIN_HL_H)}") no-repeat center/contain;
    cursor: pointer;
    transition: all 0.15s ease;
    z-index: 10;
`;

/**
 * Interactive map using MapLibre GL with OpenStreetMap tiles.
 * Supports highlighting a specific pin and flying to it.
 */
export default function MapView({ locations, highlightedId }: MapViewProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);
    const markersRef = useRef<Map<string, { marker: maplibregl.Marker; el: HTMLDivElement }>>(new Map());

    // Initialize map once
    useEffect(() => {
        if (!mapContainer.current || mapRef.current) return;

        const bounds = new maplibregl.LngLatBounds();
        locations.forEach(loc => bounds.extend([loc.longitude, loc.latitude]));

        const osmStyle: maplibregl.StyleSpecification = {
            version: 8,
            sources: {
                osm: {
                    type: 'raster',
                    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                    tileSize: 256,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                },
            },
            layers: [{
                id: 'osm-tiles',
                type: 'raster',
                source: 'osm',
                minzoom: 0,
                maxzoom: 19,
            }],
        };

        mapRef.current = new maplibregl.Map({
            container: mapContainer.current,
            style: osmStyle,
            center: locations.length > 0
                ? [bounds.getCenter().lng, bounds.getCenter().lat]
                : [-74.006, 40.7128],
            zoom: 10,
        });

        mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        if (locations.length > 0) {
            mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 14 });
        }

        // Create markers and store refs
        const markerMap = new Map<string, { marker: maplibregl.Marker; el: HTMLDivElement }>();

        locations.forEach(loc => {
            const el = document.createElement('div');
            el.className = 'marker';
            el.style.cssText = PIN_DEFAULT;

            el.addEventListener('mouseenter', () => {
                if (el.dataset.highlighted !== 'true') {
                    el.style.transform = 'scale(1.2)';
                }
            });
            el.addEventListener('mouseleave', () => {
                if (el.dataset.highlighted !== 'true') {
                    el.style.transform = 'scale(1)';
                }
            });

            const popupContent = `
                <div style="padding: 8px; max-width: 220px;">
                    <h4 style="font-weight: 600; margin-bottom: 4px; color: #111; font-size: 14px;">
                        ${loc.serviceName || loc.name}
                    </h4>
                    ${loc.name && loc.serviceName && loc.name !== loc.serviceName
                    ? `<p style="color: #666; font-size: 12px; margin-bottom: 8px;">${loc.name}</p>`
                    : ''}
                    ${loc.serviceId
                    ? `<a href="/services/${loc.serviceId}" 
                             style="color: #2563eb; font-size: 12px; text-decoration: none; display: inline-block; margin-top: 4px;">
                             View service details →
                           </a>`
                    : `<a href="/services" 
                             style="color: #2563eb; font-size: 12px; text-decoration: none; display: inline-block; margin-top: 4px;">
                             Browse services →
                           </a>`
                }
                </div>
            `;

            const popup = new maplibregl.Popup({ offset: [0, -PIN_H] }).setHTML(popupContent);
            const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
                .setLngLat([loc.longitude, loc.latitude])
                .setPopup(popup)
                .addTo(mapRef.current!);

            markerMap.set(loc.serviceId || loc.id, { marker, el });
        });

        markersRef.current = markerMap;

        return () => {
            mapRef.current?.remove();
            mapRef.current = null;
            markersRef.current.clear();
        };
    }, [locations]);

    // React to highlight changes — style the pin and fly to it
    useEffect(() => {
        const markers = markersRef.current;

        // Reset all pins to default
        markers.forEach(({ el }) => {
            el.style.cssText = PIN_DEFAULT;
            el.dataset.highlighted = 'false';
        });

        if (!highlightedId || !mapRef.current) return;

        const entry = markers.get(highlightedId);
        if (!entry) {
            // No pin for this card — fit bounds to show all pins
            const bounds = new maplibregl.LngLatBounds();
            markers.forEach(({ marker }) => bounds.extend(marker.getLngLat()));
            if (!bounds.isEmpty()) {
                mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 14, duration: 800 });
            }
            return;
        }

        // Highlight the pin
        entry.el.style.cssText = PIN_HIGHLIGHTED;
        entry.el.dataset.highlighted = 'true';

        // Fly to the highlighted pin
        const lngLat = entry.marker.getLngLat();
        mapRef.current.flyTo({
            center: [lngLat.lng, lngLat.lat],
            zoom: Math.max(mapRef.current.getZoom(), 14),
            duration: 800,
        });
    }, [highlightedId]);

    return (
        <div
            ref={mapContainer}
            className="w-full h-full"
            style={{ minHeight: '400px' }}
        />
    );
}
