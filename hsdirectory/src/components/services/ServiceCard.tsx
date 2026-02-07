import Link from 'next/link';
import { Service } from '@/lib/api';

interface ServiceCardProps {
    service: Service;
}

/**
 * Card component for displaying service summary in lists.
 * Shows name, description, organization, and status.
 */
export function ServiceCard({ service }: ServiceCardProps) {
    return (
        <Link
            href={`/services/${service.id}`}
            className="group block rounded-xl border border-gray-200 bg-white p-6 shadow-sm 
        transition-all hover:border-blue-300 hover:shadow-md
        dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-600"
        >
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                    {/* Service Name */}
                    <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 
            dark:text-white dark:group-hover:text-blue-400 truncate">
                        {service.name}
                    </h3>

                    {/* Organization */}
                    {service.organization && (
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            {service.organization.name}
                        </p>
                    )}

                    {/* Description */}
                    {service.description && (
                        <p className="mt-3 text-gray-600 dark:text-gray-300 line-clamp-2">
                            {service.description}
                        </p>
                    )}
                </div>

                {/* Status Badge */}
                {service.status && (
                    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium
            ${service.status === 'active'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                    >
                        {service.status}
                    </span>
                )}
            </div>

            {/* Footer with location hint */}
            {service.service_at_locations && service.service_at_locations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                    <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {service.service_at_locations.length} location{service.service_at_locations.length !== 1 ? 's' : ''}
                    </p>
                </div>
            )}
        </Link>
    );
}
