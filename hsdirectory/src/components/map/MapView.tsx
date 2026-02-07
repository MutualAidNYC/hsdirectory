'use client';

import { useEffect, useRef } from 'react';
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
}

/**
 * Interactive map component using MapLibre GL with OpenStreetMap tiles.
 *
 * Uses OSM raster tiles for a full-featured, real-world map layer.
 * Displays service locations with clickable markers and popups.
 */
export default function MapView({ locations }: MapViewProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);

    useEffect(() => {
        if (!mapContainer.current || map.current) return;

        // Calculate bounds to fit all markers
        const bounds = new maplibregl.LngLatBounds();
        locations.forEach(loc => {
            bounds.extend([loc.longitude, loc.latitude]);
        });

        // OpenStreetMap raster tile style definition
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
            layers: [
                {
                    id: 'osm-tiles',
                    type: 'raster',
                    source: 'osm',
                    minzoom: 0,
                    maxzoom: 19,
                },
            ],
        };

        // Initialize map
        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: osmStyle,
            center: locations.length > 0
                ? [bounds.getCenter().lng, bounds.getCenter().lat]
                : [-74.006, 40.7128], // Default to NYC
            zoom: 10,
        });

        // Add navigation controls
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        // Fit bounds if we have locations
        if (locations.length > 0) {
            map.current.fitBounds(bounds, {
                padding: 50,
                maxZoom: 14,
            });
        }

        // Add markers
        locations.forEach(loc => {
            // Create marker element
            const el = document.createElement('div');
            el.className = 'marker';
            el.style.cssText = `
                width: 28px;
                height: 28px;
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                border: 3px solid white;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                transition: box-shadow 0.15s ease, border-width 0.15s ease;
            `;
            el.addEventListener('mouseenter', () => {
                el.style.boxShadow = '0 4px 12px rgba(37,99,235,0.5)';
                el.style.borderWidth = '4px';
            });
            el.addEventListener('mouseleave', () => {
                el.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
                el.style.borderWidth = '3px';
            });

            // Create popup
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

            const popup = new maplibregl.Popup({ offset: 25 })
                .setHTML(popupContent);

            // Add marker to map
            new maplibregl.Marker({ element: el })
                .setLngLat([loc.longitude, loc.latitude])
                .setPopup(popup)
                .addTo(map.current!);
        });

        // Cleanup
        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, [locations]);

    return (
        <div
            ref={mapContainer}
            className="w-full h-full"
            style={{ minHeight: '400px' }}
        />
    );
}
