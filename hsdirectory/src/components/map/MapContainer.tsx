'use client';

import dynamic from 'next/dynamic';

interface MapLocation {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    serviceName?: string;
    serviceId?: string;
}

interface MapContainerProps {
    locations: MapLocation[];
}

// Dynamically import MapView to avoid SSR issues with MapLibre
const MapView = dynamic(() => import('./MapView'), {
    ssr: false,
    loading: () => (
        <div className="w-full h-[600px] bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
            <div className="text-gray-500 dark:text-gray-400">Loading map...</div>
        </div>
    ),
});

/**
 * Client-side container for the map.
 * Handles dynamic import of MapView to avoid SSR issues.
 */
export function MapContainer({ locations }: MapContainerProps) {
    return <MapView locations={locations} />;
}
