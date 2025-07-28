// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import {
  FolderIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  UsersIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { projectsAPI, adminAPI } from '../utils/api';
import { useAuth } from '../utils/auth';
import LoadingSpinner from '../components/LoadingSpinner';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const { user, isAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentProjects, setRecentProjects] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load projects
      const projectsResponse = await projectsAPI.getAll({ page: 1, per_page: 5 });
      if (projectsResponse.data.success) {
        setRecentProjects(projectsResponse.data.projects);
      }

      // Load system status if admin
      if (isAdmin()) {
        try {
          const statusResponse = await adminAPI.getSystemStatus();
          if (statusResponse.data.success) {
            setSystemStatus(statusResponse.data.status);
          }
        } catch (error) {
          console.error('Failed to load system status:', error);
        }
      }

      // Mock stats for now (in real app, this would come from API)
      setStats({
        totalProjects: projectsResponse.data.pagination?.total || 0,
        totalWebsites: 25,
        totalPages: 1250,
        totalSnippets: 3420
      });

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const mockChartData = [
    { name: 'Mon', pages: 120, snippets: 340 },
    { name: 'Tue', pages: 190, snippets: 420 },
    { name: 'Wed', pages: 350, snippets: 680 },
    { name: 'Thu', pages: 280, snippets: 590 },
    { name: 'Fri', pages: 420, snippets: 890 },
    { name: 'Sat', pages: 150, snippets: 320 },
    { name: 'Sun', pages: 80, snippets: 180 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Projects',
      value: stats?.totalProjects || 0,
      icon: FolderIcon,
      color: 'bg-blue-500',
      change: '+12%',
      changeType: 'positive'
    },
    {
      name: 'Active Websites',
      value: stats?.totalWebsites || 0,
      icon: GlobeAltIcon,
      color: 'bg-green-500',
      change: '+8%',
      changeType: 'positive'
    },
    {
      name: 'Pages Scraped',
      value: stats?.totalPages || 0,
      icon: DocumentTextIcon,
      color: 'bg-purple-500',
      change: '+24%',
      changeType: 'positive'
    },
    {
      name: 'Content Snippets',
      value: stats?.totalSnippets || 0,
      icon: ArrowTrendingUpIcon,
      color: 'bg-orange-500',
      change: '+15%',
      changeType: 'positive'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">
          Welcome back, {user?.first_name}! Here's what's happening with your scraping projects.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value.toLocaleString()}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Weekly Activity</h3>
            <p className="text-sm text-gray-600">Pages scraped and snippets extracted</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="pages" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="snippets" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Projects */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Recent Projects</h3>
                <p className="text-sm text-gray-600">Your latest scraping projects</p>
              </div>
              <Link to="/projects" className="text-sm text-blue-600 hover:text-blue-500">
                View all
              </Link>
            </div>
          </div>
          <div className="space-y-4">
            {recentProjects.length > 0 ? (
              recentProjects.map((project) => (
                <div key={project.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <FolderIcon className="h-6 w-6 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{project.name}</p>
                      <p className="text-xs text-gray-500">
                        {project.websites_count || 0} websites • {project.pages_scraped || 0} pages
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      project.status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.status}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6">
                <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
                <div className="mt-6">
                  <Link to="/projects/new" className="btn-primary">
                    Create Project
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Status (Admin Only) */}
      {isAdmin() && systemStatus && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">System Status</h3>
            <p className="text-sm text-gray-600">Database and system statistics</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(systemStatus.table_statistics || {}).map(([table, count]) => (
              <div key={table} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-sm text-gray-600 capitalize">{table}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;