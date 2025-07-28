// frontend/src/pages/ProjectDetail.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  PlusIcon,
  PlayIcon,
  EyeIcon,
  ClockIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import { projectsAPI, websitesAPI, scrapingAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [websites, setWebsites] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadProjectDetails();
  }, [id]);

  const loadProjectDetails = async () => {
    try {
      setLoading(true);
      
      // Load project details
      const projectResponse = await projectsAPI.getById(id);
      if (projectResponse.data.success) {
        setProject(projectResponse.data.project);
      }

      // Load project statistics
      try {
        const statsResponse = await projectsAPI.getStatistics(id);
        if (statsResponse.data.success) {
          setStatistics(statsResponse.data.statistics);
        }
      } catch (error) {
        console.error('Failed to load statistics:', error);
      }

    } catch (error) {
      console.error('Error loading project details:', error);
      toast.error('Failed to load project details');
      navigate('/projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await projectsAPI.delete(id);
      if (response.data.success) {
        toast.success('Project deleted successfully');
        navigate('/projects');
      } else {
        toast.error('Failed to delete project');
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      toast.error('Failed to delete project');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'archived':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-blue-100 text-blue-800';
      case 'low':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Project not found</h3>
        <p className="text-gray-600 mt-2">The project you're looking for doesn't exist.</p>
        <Link to="/projects" className="btn-primary mt-4">
          Back to Projects
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: EyeIcon },
    { id: 'websites', name: 'Websites', icon: GlobeAltIcon },
    { id: 'content', name: 'Content', icon: DocumentTextIcon },
    { id: 'settings', name: 'Settings', icon: PencilIcon }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/projects')}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-gray-600">{project.description}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <span className={`badge ${getStatusColor(project.status)}`}>
            {project.status}
          </span>
          {project.priority && (
            <span className={`badge ${getPriorityColor(project.priority)}`}>
              {project.priority} priority
            </span>
          )}
          
          <button className="btn-secondary">
            <PencilIcon className="h-4 w-4 mr-2" />
            Edit
          </button>
          
          <button
            onClick={handleDeleteProject}
            className="btn-danger"
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Delete
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <GlobeAltIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {project.websites_count || 0}
              </p>
              <p className="text-sm text-gray-600">Websites</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {project.pages_scraped || 0}
              </p>
              <p className="text-sm text-gray-600">Pages Scraped</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {project.snippets_count || 0}
              </p>
              <p className="text-sm text-gray-600">Content Snippets</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <ClockIcon className="h-8 w-8 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">
                {project.last_crawl ? new Date(project.last_crawl).toLocaleDateString() : 'Never'}
              </p>
              <p className="text-sm text-gray-600">Last Crawl</p>
            </div>
          </div>
        </div>
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
            {/* Project Information */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Project Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Owner</p>
                  <p className="text-sm text-gray-900">{project.owner_name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Industry</p>
                  <p className="text-sm text-gray-900">{project.industry || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Created</p>
                  <p className="text-sm text-gray-900">
                    {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Last Updated</p>
                  <p className="text-sm text-gray-900">
                    {new Date(project.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              {project.tags && project.tags.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-600 mb-2">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {project.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recent Activity */}
            {statistics?.recent_activity && (
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  {statistics.recent_activity.length > 0 ? (
                    statistics.recent_activity.map((activity, index) => (
                      <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <DocumentTextIcon className="h-5 w-5 text-gray-400" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                          <p className="text-sm text-gray-600">{activity.url}</p>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-600">No recent activity</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'websites' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Websites</h3>
              <Link to={`/websites?project=${id}`} className="btn-primary">
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Website
              </Link>
            </div>
            
            <div className="card">
              <p className="text-gray-600 text-center py-8">
                No websites configured yet. Add a website to start scraping.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Content Review</h3>
              <Link to={`/content?project=${id}`} className="btn-primary">
                <EyeIcon className="h-4 w-4 mr-2" />
                Review Content
              </Link>
            </div>
            
            <div className="card">
              <p className="text-gray-600 text-center py-8">
                No content extracted yet. Start scraping to generate content snippets.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Project Settings</h3>
              <p className="text-gray-600">
                Project settings management will be available in a future update.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectDetail;