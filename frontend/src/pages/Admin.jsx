// frontend/src/pages/Admin.jsx
import React, { useState, useEffect } from 'react';
import {
  UsersIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ComputerDesktopIcon,
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { adminAPI } from '../utils/api';
import { useAuth } from '../utils/auth';
import LoadingSpinner from '../components/LoadingSpinner';
import SqlExecutor from '../components/SqlExecutor';
import toast from 'react-hot-toast';

const Admin = () => {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [systemStatus, setSystemStatus] = useState(null);
  const [users, setUsers] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAdmin()) {
      toast.error('Admin access required');
      return;
    }
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      
      // Load system status
      try {
        const statusResponse = await adminAPI.getSystemStatus();
        if (statusResponse.data.success) {
          setSystemStatus(statusResponse.data.status);
        }
      } catch (error) {
        console.error('Failed to load system status:', error);
      }

      // Load users
      try {
        const usersResponse = await adminAPI.getUsers();
        if (usersResponse.data.success) {
          setUsers(usersResponse.data.users);
        }
      } catch (error) {
        console.error('Failed to load users:', error);
      }

      // Load settings
      try {
        const settingsResponse = await adminAPI.getSettings();
        if (settingsResponse.data.success) {
          setSettings(settingsResponse.data.settings);
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
      }

    } catch (error) {
      console.error('Error loading admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  if (!isAdmin()) {
    return (
      <div className="text-center py-12">
        <ShieldCheckIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-500">
          You need administrator privileges to access this page.
        </p>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'users', name: 'Users', icon: UsersIcon },
    { id: 'sql', name: 'SQL Executor', icon: ComputerDesktopIcon },
    { id: 'settings', name: 'Settings', icon: Cog6ToothIcon }
  ];

  const formatBytes = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-gray-600">
          System administration, user management, and advanced configuration.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-5 w-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* System Health */}
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900">System Health</h3>
                <p className="text-sm text-gray-600">Current system status and performance</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex items-center">
                  <CheckCircleIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">Database</p>
                    <p className="text-sm text-green-600">Connected</p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <CheckCircleIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">API Server</p>
                    <p className="text-sm text-green-600">Running</p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  {settings?.azure_openai?.available ? (
                    <CheckCircleIcon className="h-8 w-8 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />
                  )}
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900">Azure OpenAI</p>
                    <p className={`text-sm ${settings?.azure_openai?.available ? 'text-green-600' : 'text-yellow-600'}`}>
                      {settings?.azure_openai?.available ? 'Available' : 'Not Configured'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Database Statistics */}
            {systemStatus?.table_statistics && (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-medium text-gray-900">Database Statistics</h3>
                  <p className="text-sm text-gray-600">Record counts across all tables</p>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(systemStatus.table_statistics).map(([table, count]) => (
                    <div key={table} className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{count}</div>
                      <div className="text-sm text-gray-600 capitalize">{table}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Activity */}
            {systemStatus?.recent_activity_24h && (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-medium text-gray-900">Recent Activity (24h)</h3>
                  <p className="text-sm text-gray-600">Most frequent user actions</p>
                </div>
                
                <div className="space-y-3">
                  {systemStatus.recent_activity_24h.length > 0 ? (
                    systemStatus.recent_activity_24h.map((activity, index) => (
                      <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                        <span className="text-sm font-medium text-gray-900 capitalize">
                          {activity.action.replace('_', ' ')}
                        </span>
                        <span className="text-sm text-gray-600">{activity.count} times</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No recent activity recorded</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">User Management</h3>
              <button className="btn-primary">
                <UsersIcon className="h-4 w-4 mr-2" />
                Add User
              </button>
            </div>

            <div className="card">
              {users.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Last Login
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {user.full_name}
                              </div>
                              <div className="text-sm text-gray-500">{user.email}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              user.role === 'admin' 
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              user.is_active 
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.last_login 
                              ? new Date(user.last_login).toLocaleDateString()
                              : 'Never'
                            }
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-blue-600 hover:text-blue-900 mr-4">
                              Edit
                            </button>
                            <button className="text-red-600 hover:text-red-900">
                              Disable
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <UsersIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Unable to load user data. Check system configuration.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'sql' && (
          <div>
            <SqlExecutor />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900">Application Settings</h3>
                <p className="text-sm text-gray-600">System configuration and preferences</p>
              </div>

              {settings ? (
                <div className="space-y-6">
                  {/* Azure OpenAI Settings */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Azure OpenAI Configuration</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Status</label>
                        <div className="mt-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            settings.azure_openai?.available 
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {settings.azure_openai?.available ? 'Available' : 'Not Configured'}
                          </span>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Model</label>
                        <p className="mt-1 text-sm text-gray-900">
                          {settings.azure_openai?.model || 'Not configured'}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Deployment</label>
                        <p className="mt-1 text-sm text-gray-900">
                          {settings.azure_openai?.deployment || 'Not configured'}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Endpoint</label>
                        <p className="mt-1 text-sm text-gray-900">
                          {settings.azure_openai?.endpoint_configured ? 'Configured' : 'Not configured'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Application Settings */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Application Configuration</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Application Name</label>
                        <p className="mt-1 text-sm text-gray-900">{settings.app?.name}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Version</label>
                        <p className="mt-1 text-sm text-gray-900">{settings.app?.version}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Flask Port</label>
                        <p className="mt-1 text-sm text-gray-900">{settings.app?.flask_port}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">React Port</label>
                        <p className="mt-1 text-sm text-gray-900">{settings.app?.react_port}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Debug Mode</label>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          settings.app?.debug 
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {settings.app?.debug ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Database Settings */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Database Configuration</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Database File</label>
                        <p className="mt-1 text-sm text-gray-900">{settings.database?.uri}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">SQL Echo</label>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          settings.database?.echo 
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {settings.database?.echo ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Cog6ToothIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Settings not available</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Unable to load system settings. Check your permissions.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;