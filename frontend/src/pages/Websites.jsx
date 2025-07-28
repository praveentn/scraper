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
    } else {
      setWebsites([]);
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
        await loadWebsites(selectedProject);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadWebsites = async (projectId) => {
    try {
      setLoading(true);
      // **FIX: Use the correct API endpoint**
      const response = await projectsAPI.getProjectWebsites(projectId);
      
      if (response.data.success) {
        setWebsites(response.data.websites || []);
      } else {
        console.error('Failed to load websites:', response.data.message);
        setWebsites([]);
      }
    } catch (error) {
      console.error('Error loading websites:', error);
      setWebsites([]);
      // Don't show error toast here as it might be a new project with no websites
    } finally {
      setLoading(false);
    }
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
        await loadWebsites(selectedProject);
      } else {
        toast.error(response.data.message || 'Failed to add website');
      }
    } catch (error) {
      console.error('Error adding website:', error);
      toast.error('Failed to add website');
    }
  };

  const handleDeleteWebsite = async (websiteId) => {
    if (!window.confirm('Are you sure you want to delete this website?')) {
      return;
    }

    try {
      const response = await websitesAPI.delete(websiteId);
      
      if (response.data.success) {
        toast.success('Website deleted successfully');
        await loadWebsites(selectedProject);
      } else {
        toast.error(response.data.message || 'Failed to delete website');
      }
    } catch (error) {
      console.error('Error deleting website:', error);
      toast.error('Failed to delete website');
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
        // Refresh the list to show updated status
        await loadWebsites(selectedProject);
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
          disabled={!selectedProject}
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
          <option value="">Select a Project</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* Websites List */}
      {!selectedProject ? (
        <div className="text-center py-12">
          <GlobeAltIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Select a project</h3>
          <p className="mt-1 text-sm text-gray-500">
            Choose a project from the dropdown to view and manage its websites.
          </p>
        </div>
      ) : websites.length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {websites.map((website) => (
              <li key={website.id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <GlobeAltIcon className="h-10 w-10 text-gray-400" />
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-gray-900">
                          {website.name || 'Unnamed Website'}
                        </p>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(website.status)}`}>
                          {website.status || 'inactive'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">{website.url}</p>
                      {website.description && (
                        <p className="text-sm text-gray-400 mt-1">{website.description}</p>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>Depth: {website.crawl_depth}</span>
                        <span>Rate: {website.rate_limit_delay}s</span>
                        <span>Pages: {website.pages_scraped || 0}</span>
                        {website.last_scraped && (
                          <span>Last: {new Date(website.last_scraped).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleStartScraping(website.id)}
                      className="p-2 text-green-600 hover:text-green-900"
                      title="Start Scraping"
                    >
                      <PlayIcon className="h-5 w-5" />
                    </button>
                    <Link
                      to={`/content?project=${selectedProject}&website=${website.id}`}
                      className="p-2 text-blue-600 hover:text-blue-900"
                      title="View Content"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </Link>
                    <Link
                      to={`/reports?project=${selectedProject}&website=${website.id}`}
                      className="p-2 text-purple-600 hover:text-purple-900"
                      title="View Reports"
                    >
                      <ChartBarIcon className="h-5 w-5" />
                    </Link>
                    <button
                      onClick={() => handleDeleteWebsite(website.id)}
                      className="p-2 text-red-600 hover:text-red-900"
                      title="Delete Website"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="text-center py-12">
          <GlobeAltIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No websites found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding a website to this project.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary flex items-center mx-auto"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Website
            </button>
          </div>
        </div>
      )}

      {/* Add Website Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Add Website</h3>
              
              <form onSubmit={handleAddWebsite} className="space-y-4">
                {/* Project Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Project</label>
                  <select
                    value={formData.project_id}
                    onChange={(e) => setFormData({...formData, project_id: e.target.value})}
                    className="input-field"
                    required
                  >
                    <option value="">Select Project</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">URL</label>
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
                  <label className="block text-sm font-medium text-gray-700">Name (Optional)</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="input-field"
                    placeholder="Friendly name for this website"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description (Optional)</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="input-field"
                    rows="3"
                    placeholder="Brief description of this website"
                  />
                </div>

                {/* Crawl Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Crawl Depth</label>
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
                    <label className="block text-sm font-medium text-gray-700">Rate Limit (seconds)</label>
                    <input
                      type="number"
                      min="0.1"
                      max="60"
                      step="0.1"
                      value={formData.rate_limit_delay}
                      onChange={(e) => setFormData({...formData, rate_limit_delay: parseFloat(e.target.value)})}
                      className="input-field"
                    />
                  </div>
                </div>

                {/* Checkboxes */}
                <div className="space-y-2">
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
        </div>
      )}
    </div>
  );
};

export default Websites;