// frontend/src/components/Layout.jsx  
import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../utils/auth';
import Header from './Header';
import Sidebar from './Sidebar';
import LoadingSpinner from './LoadingSpinner';

const Layout = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 lg:ml-64">
          <div className="py-6">
            <div className="mx-auto px-4 sm:px-6 lg:px-8">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;