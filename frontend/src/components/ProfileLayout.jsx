import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { User, Settings, Ticket, LogOut, Package } from 'lucide-react';
import { useAuth } from '../App';

const ProfileLayout = ({ children }) => {
  const { logout, user } = useAuth();
  const location = useLocation();

  const menuItems = [
    {
      path: '/profile',
      label: 'My Profile',
      icon: User,
      exact: true
    },
    {
      path: '/profile/settings',
      label: 'Settings',
      icon: Settings
    },
    ...(user?.role !== 'admin' ? [
      {
        path: '/profile/tickets',
        label: 'My Tickets',
        icon: Ticket
      },
      {
        path: '/profile/orders',
        label: 'Order History',
        icon: Package
      }
    ] : [])
  ];

  const isActive = (path, exact = false) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  // Hide sidebar for admin users
  const showSidebar = user?.role !== 'admin';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          <nav className="flex md:flex-col items-center md:items-stretch gap-2 overflow-x-auto md:overflow-visible pb-2 md:pb-0">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive(item.path, item.exact)
                      ? 'bg-blue-50 text-blue-700 border-r-4 border-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}

            <div className="pt-4 border-t">
              <Button
                onClick={logout}
                variant="ghost"
                className="w-full justify-start text-gray-700 hover:bg-red-50 hover:text-red-700"
              >
                <LogOut className="h-5 w-5 mr-3" />
                <span className="font-medium">Logout</span>
              </Button>
            </div>
          </nav>
          <div className="flex-1">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileLayout;
