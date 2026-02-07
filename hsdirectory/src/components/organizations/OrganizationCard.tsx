import Link from 'next/link';
import { Organization } from '@/lib/api';

interface OrganizationCardProps {
    organization: Organization;
}

/**
 * Card component for displaying organization summary in lists.
 */
export function OrganizationCard({ organization }: OrganizationCardProps) {
    return (
        <Link
            href={`/organizations/${organization.id}`}
            className="group block rounded-xl border border-gray-200 bg-white p-6 shadow-sm 
        transition-all hover:border-blue-300 hover:shadow-md
        dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-600"
        >
            <div className="flex items-start gap-4">
                {/* Logo or Placeholder */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg 
          bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600 font-bold text-lg
          dark:from-blue-900 dark:to-blue-800 dark:text-blue-300">
                    {organization.logo ? (
                        <img
                            src={organization.logo}
                            alt={organization.name}
                            className="h-full w-full object-contain rounded-lg"
                        />
                    ) : (
                        organization.name.charAt(0).toUpperCase()
                    )}
                </div>

                <div className="flex-1 min-w-0">
                    {/* Organization Name */}
                    <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 
            dark:text-white dark:group-hover:text-blue-400 truncate">
                        {organization.name}
                    </h3>

                    {/* Description */}
                    {organization.description && (
                        <p className="mt-2 text-gray-600 dark:text-gray-300 line-clamp-2">
                            {organization.description}
                        </p>
                    )}

                    {/* Service Count and Links */}
                    <div className="mt-3 flex flex-wrap gap-3 text-sm">
                        {organization.service_count !== undefined && organization.service_count > 0 && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                </svg>
                                {organization.service_count} {organization.service_count === 1 ? 'Service' : 'Services'}
                            </span>
                        )}
                        {organization.url && (
                            <span className="text-blue-600 dark:text-blue-400 flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                </svg>
                                Website
                            </span>
                        )}
                        {organization.email && (
                            <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                Email
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </Link>
    );
}
