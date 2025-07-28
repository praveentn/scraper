// frontend/src/pages/Websites.jsx
import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  PlusIcon,
  GlobeAltIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
  EyeIcon,
  ChartBarIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { projectsAPI, websitesAPI, scrapingAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Websites = () => {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project');
  
  const [websites, setWebsites] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(projectId || '');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    project_id: projectId || '',
    url: '',
    name: '',
    description: '',
    crawl_depth: 2,
    follow_external_links: false,
    respect_robots_txt: true,
    rate_limit_delay: 1.0
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadWebsites(selectedProject);
    }
  }, [selectedProject]);

  const loadData = async () => {
    try {
      // Load projects for dropdown
      const projectsResponse = await projectsAPI.getAll({ per_page: 100 });
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.projects);
      }

      // Load websites if project is selected
      if (selectedProject) {
        loadWebsites(selectedProject);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadWebsites = async (projectId) => {
    // For now, return empty array since we don't have a specific endpoint
    // In a real implementation, this would call an API to get websites for the project
    setWebsites([]);
  };

  const handleAddWebsite = async (e) => {
    e.preventDefault();
    
    if (!formData.project_id || !formData.url) {
      toast.error('Project and URL are required');
      return;
    }

    try {
      const response = await websitesAPI.create(formData);
      
      if (response.data.success) {
        toast.success('Website added successfully');
        setShowAddModal(false);
        setFormData({
          project_id: selectedProject,
          url: '',
          name: '',
          description: '',
          crawl_depth: 2,
          follow_external_links: false,
          respect_robots_txt: true,
          rate_limit_delay: 1.0
        });
        loadWebsites(selectedProject);
      } else {
        toast.error(response.data.message || 'Failed to add website');
      }
    } catch (error) {
      console.error('Error adding website:', error);
      toast.error('Failed to add website');
    }
  };

  const handleStartScraping = async (websiteId) => {
    try {
      const response = await scrapingAPI.run({
        website_id: websiteId,
        use_selenium: false
      });
      
      if (response.data.success) {
        toast.success('Scraping started successfully');
      } else {
        toast.error(response.data.message || 'Failed to start scraping');
      }
    } catch (error) {
      console.error('Error starting scraping:', error);
      toast.error('Failed to start scraping');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Websites</h1>
          <p className="text-gray-600">
            Configure and manage websites for scraping across your projects.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Website
        </button>
      </div>

      {/* Project Filter */}
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">Filter by project:</label>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="input-field w-64"
        >
          <option value="">All Projects</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* Websites List */}
      {websites.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {websites.map((website) => (
            <div key={website.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <GlobeAltIcon className="h-8 w-8 text-blue-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">
                      {website.name || new URL(website.url).hostname}
                    </h3>
                    <p className="text-sm text-blue-600 hover:text-blue-500">
                      <a href={website.url} target="_blank" rel="noopener noreferrer">
                        {website.url}
                      </a>
                    </p>
                    {website.description && (
                      <p className="text-sm text-gray-600 mt-1">{website.description}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`badge ${getStatusColor(website.status)}`}>
                    {website.status}
                  </span>
                  
                  <button
                    onClick={() => handleStartScraping(website.id)}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="Start Scraping"
                  >
                    <PlayIcon className="h-5 w-5" />
                  </button>
                  
                  <button className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  
                  <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Website Stats */}
              <div className="mt-4 grid grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {website.total_pages || 0}
                  </div>
                  <div className="text-xs text-gray-500">Pages</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {website.crawl_depth}
                  </div>
                  <div className="text-xs text-gray-500">Max Depth</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {website.rate_limit_delay}s
                  </div>
                  <div className="text-xs text-gray-500">Delay</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-gray-600">
                    {website.last_crawled 
                      ? new Date(website.last_crawled).toLocaleDateString()
                      : 'Never'
                    }
                  </div>
                  <div className="text-xs text-gray-500">Last Crawl</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <GlobeAltIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No websites configured</h3>
          <p className="mt-1 text-sm text-gray-500">
            {selectedProject 
              ? 'Add a website to start scraping for this project.'
              : 'Select a project and add websites to start scraping.'
            }
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Website
            </button>
          </div>
        </div>
      )}

      {/* Add Website Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Add Website</h3>
            </div>
            
            <form onSubmit={handleAddWebsite} className="p-6 space-y-4">
              {/* Project Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project *
                </label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData({...formData, project_id: e.target.value})}
                  className="input-field"
                  required
                >
                  <option value="">Select a project</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Website URL *
                </label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({...formData, url: e.target.value})}
                  className="input-field"
                  placeholder="https://example.com"
                  required
                />
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="input-field"
                  placeholder="Optional display name"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="input-field resize-none"
                  rows={3}
                  placeholder="Optional description"
                />
              </div>

              {/* Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Crawl Depth
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={formData.crawl_depth}
                    onChange={(e) => setFormData({...formData, crawl_depth: parseInt(e.target.value)})}
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rate Limit (seconds)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={formData.rate_limit_delay}
                    onChange={(e) => setFormData({...formData, rate_limit_delay: parseFloat(e.target.value)})}
                    className="input-field"
                  />
                </div>
              </div>

              {/* Checkboxes */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.follow_external_links}
                    onChange={(e) => setFormData({...formData, follow_external_links: e.target.checked})}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Follow external links</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.respect_robots_txt}
                    onChange={(e) => setFormData({...formData, respect_robots_txt: e.target.checked})}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Respect robots.txt</span>
                </label>
              </div>

              {/* Form Actions */}
              <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Add Website
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Websites;