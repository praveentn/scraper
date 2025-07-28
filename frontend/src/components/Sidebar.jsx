// frontend/src/components/Sidebar.jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  FolderIcon,
  GlobeAltIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../utils/auth';
import classNames from 'classnames';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Projects', href: '/projects', icon: FolderIcon },
  { name: 'Websites', href: '/websites', icon: GlobeAltIcon },
  { name: 'Scraper', href: '/scraper', icon: CpuChipIcon },
  { name: 'Content', href: '/content', icon: DocumentTextIcon },
  { name: 'Reports', href: '/reports', icon: ChartBarIcon },
];

const adminNavigation = [
  { name: 'Admin', href: '/admin', icon: Cog6ToothIcon },
];

const Sidebar = () => {
  const location = useLocation();
  const { isAdmin } = useAuth();

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
        <div className="flex h-16 shrink-0 items-center">
          <div className="flex items-center space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <span className="text-sm font-bold text-white">B</span>
            </div>
            <span className="text-xl font-bold text-gray-900">Blitz</span>
          </div>
        </div>
        
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <li key={item.name}>
                      <Link
                        to={item.href}
                        className={classNames(
                          'sidebar-nav-item',
                          isActive ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
                        )}
                      >
                        <item.icon className="h-5 w-5 shrink-0" />
                        {item.name}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </li>
            
            {/* Quick Actions */}
            <li>
              <div className="text-xs font-semibold leading-6 text-gray-400">Quick Actions</div>
              <ul role="list" className="-mx-2 mt-2 space-y-1">
                <li>
                  <Link
                    to="/projects/new"
                    className="sidebar-nav-item sidebar-nav-item-inactive"
                  >
                    <PlusIcon className="h-5 w-5 shrink-0" />
                    New Project
                  </Link>
                </li>
              </ul>
            </li>

            {/* Admin Section */}
            {isAdmin() && (
              <li>
                <div className="text-xs font-semibold leading-6 text-gray-400">Administration</div>
                <ul role="list" className="-mx-2 mt-2 space-y-1">
                  {adminNavigation.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                      <li key={item.name}>
                        <Link
                          to={item.href}
                          className={classNames(
                            'sidebar-nav-item',
                            isActive ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
                          )}
                        >
                          <item.icon className="h-5 w-5 shrink-0" />
                          {item.name}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </li>
            )}
          </ul>
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;