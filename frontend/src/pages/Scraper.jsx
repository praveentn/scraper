// frontend/src/pages/Scraper.jsx
import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  ClockIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import { projectsAPI, scrapingAPI, websitesAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Scraper = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [websites, setWebsites] = useState([]);
  const [scrapingJobs, setScrapingJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSinglePageModal, setShowSinglePageModal] = useState(false);
  const [singlePageForm, setSinglePageForm] = useState({
    website_id: '',
    url: '',
    use_selenium: false
  });

  useEffect(() => {
    loadData();
    // Set up polling for job status updates
    const interval = setInterval(loadScrapingJobs, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadProjectWebsites(selectedProject);
    } else {
      setWebsites([]);
    }
  }, [selectedProject]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load projects
      const projectsResponse = await projectsAPI.getAll({ per_page: 100 });
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.projects);
      }

      // Load scraping jobs
      await loadScrapingJobs();
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadProjectWebsites = async (projectId) => {
    try {
      const response = await projectsAPI.getProjectWebsites(projectId);
      if (response.data.success) {
        setWebsites(response.data.websites || []);
      }
    } catch (error) {
      console.error('Error loading websites:', error);
      setWebsites([]);
    }
  };

  const loadScrapingJobs = async () => {
    try {
      // **FIX: Use real API instead of mock data**
      const response = await scrapingAPI.getJobs({ 
        per_page: 50,
        project_id: selectedProject || undefined 
      });
      
      if (response.data.success) {
        setScrapingJobs(response.data.jobs || []);
      }
    } catch (error) {
      console.error('Error loading scraping jobs:', error);
      // Don't show error toast as this might be expected for new installations
    }
  };

  const handleStartScraping = async (websiteId) => {
    try {
      const response = await scrapingAPI.run({
        website_id: websiteId,
        use_selenium: false,
        extract_content: true
      });
      
      if (response.data.success) {
        toast.success('Scraping started successfully');
        await loadScrapingJobs();
      } else {
        toast.error(response.data.message || 'Failed to start scraping');
      }
    } catch (error) {
      console.error('Error starting scraping:', error);
      toast.error('Failed to start scraping');
    }
  };

  const handleStopScraping = async (websiteId) => {
    try {
      // **FIX: Use correct API endpoint**
      const response = await scrapingAPI.stop(websiteId);
      
      if (response.data.success) {
        toast.success('Scraping stopped successfully');
        await loadScrapingJobs();
      } else {
        toast.error(response.data.message || 'Failed to stop scraping');
      }
    } catch (error) {
      console.error('Error stopping scraping:', error);
      toast.error('Failed to stop scraping');
    }
  };

  const handleSinglePageScrape = async (e) => {
    e.preventDefault();
    
    if (!singlePageForm.url) {
      toast.error('URL is required');
      return;
    }

    try {
      const response = await scrapingAPI.run({
        url: singlePageForm.url,
        use_selenium: singlePageForm.use_selenium,
        single_page: true,
        extract_content: true
      });
      
      if (response.data.success) {
        toast.success('Single page scraping started');
        setShowSinglePageModal(false);
        setSinglePageForm({
          website_id: '',
          url: '',
          use_selenium: false
        });
        await loadScrapingJobs();
      } else {
        toast.error(response.data.message || 'Failed to start single page scraping');
      }
    } catch (error) {
      console.error('Error starting single page scraping:', error);
      toast.error('Failed to start single page scraping');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <CpuChipIcon className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />;
      case 'paused':
        return <PauseIcon className="h-5 w-5 text-yellow-600" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (startTime) => {
    if (!startTime) return 'N/A';
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
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
          <h1 className="text-2xl font-bold text-gray-900">Scraper</h1>
          <p className="text-gray-600">
            Monitor and control web scraping operations across your projects.
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowSinglePageModal(true)}
            className="btn-secondary flex items-center"
          >
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            Scrape Single Page
          </button>
          <button
            onClick={() => loadScrapingJobs()}
            className="btn-primary flex items-center"
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" />
            Refresh
          </button>
        </div>
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

      {/* Quick Actions for Websites */}
      {selectedProject && websites.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {websites.map((website) => (
              <div key={website.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      {website.name || website.url}
                    </h4>
                    <p className="text-xs text-gray-500 truncate">{website.url}</p>
                  </div>
                  <button
                    onClick={() => handleStartScraping(website.id)}
                    className="p-2 text-green-600 hover:text-green-900"
                    title="Start Scraping"
                  >
                    <PlayIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Scraping Jobs */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Active Scraping Jobs
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Current and recent scraping operations.
          </p>
        </div>
        
        {scrapingJobs.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {scrapingJobs.map((job) => (
              <li key={job.id}>
                <div className="px-4 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        {getStatusIcon(job.status)}
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900">
                            {job.website_name || job.website_url}
                          </p>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500">{job.website_url}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span>Project: {job.project_name}</span>
                          <span>Pages: {job.pages_scraped}/{job.total_pages || '?'}</span>
                          <span>Duration: {formatDuration(job.started_at)}</span>
                          {job.progress_percentage > 0 && (
                            <span>Progress: {job.progress_percentage}%</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {job.status === 'running' && (
                        <button
                          onClick={() => handleStopScraping(job.website_id)}
                          className="p-2 text-red-600 hover:text-red-900"
                          title="Stop Scraping"
                        >
                          <StopIcon className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {/* Progress Bar */}
                  {job.total_pages > 0 && (
                    <div className="mt-3">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${job.progress_percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center py-8">
            <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No active scraping jobs</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start scraping from the websites page or use single page scraping.
            </p>
          </div>
        )}
      </div>

      {/* Single Page Scrape Modal */}
      {showSinglePageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Scrape Single Page</h3>
              
              <form onSubmit={handleSinglePageScrape} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">URL</label>
                  <input
                    type="url"
                    value={singlePageForm.url}
                    onChange={(e) => setSinglePageForm({...singlePageForm, url: e.target.value})}
                    className="input-field"
                    placeholder="https://example.com/page"
                    required
                  />
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={singlePageForm.use_selenium}
                      onChange={(e) => setSinglePageForm({...singlePageForm, use_selenium: e.target.checked})}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Use Selenium (for JavaScript content)</span>
                  </label>
                </div>

                <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setShowSinglePageModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    Start Scraping
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

export default Scraper;