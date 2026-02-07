'use client';

import dynamic from 'next/dynamic';

interface ServiceLocationMapProps {
    latitude: number;
    longitude: number;
    name: string;
}

const MapViewDynamic = dynamic(
    () => import('@/components/map/MapView'),
    {
        ssr: false,
        loading: () => (
            <div className="w-full h-64 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <div className="text-gray-500">Loading map...</div>
            </div>
        )
    }
);

/**
 * Small map showing a single service location.
 */
export default function ServiceLocationMap({ latitude, longitude, name }: ServiceLocationMapProps) {
    const locations = [{
        id: 'service-location',
        name,
        latitude,
        longitude,
        serviceName: name,
    }];

    return (
        <div className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 h-64">
            <MapViewDynamic locations={locations} />
        </div>
    );
}
