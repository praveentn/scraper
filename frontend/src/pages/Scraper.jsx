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
import { projectsAPI, scrapingAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Scraper = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
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
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load projects
      const projectsResponse = await projectsAPI.getAll({ per_page: 100 });
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.projects);
      }

      // Mock scraping jobs data (in real app, this would come from API)
      setScrapingJobs([
        {
          id: 1,
          website_name: 'Example Site',
          website_url: 'https://example.com',
          status: 'running',
          pages_scraped: 45,
          total_pages: 120,
          started_at: new Date(Date.now() - 300000).toISOString(),
          last_activity: new Date().toISOString()
        },
        {
          id: 2,
          website_name: 'Test Site',
          website_url: 'https://test.com',
          status: 'completed',
          pages_scraped: 87,
          total_pages: 87,
          started_at: new Date(Date.now() - 3600000).toISOString(),
          completed_at: new Date(Date.now() - 300000).toISOString()
        }
      ]);

    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
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
        loadData();
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
      const response = await scrapingAPI.stop(websiteId);
      
      if (response.data.success) {
        toast.success('Scraping stopped successfully');
        loadData();
      } else {
        toast.error(response.data.message || 'Failed to stop scraping');
      }
    } catch (error) {
      console.error('Error stopping scraping:', error);
      toast.error('Failed to stop scraping');
    }
  };

  const handleSinglePageScraping = async (e) => {
    e.preventDefault();
    
    if (!singlePageForm.url) {
      toast.error('URL is required');
      return;
    }

    try {
      const response = await scrapingAPI.run({
        website_id: singlePageForm.website_id || null,
        single_page: true,
        url: singlePageForm.url,
        use_selenium: singlePageForm.use_selenium
      });
      
      if (response.data.success) {
        toast.success('Single page scraped successfully');
        setShowSinglePageModal(false);
        setSinglePageForm({ website_id: '', url: '', use_selenium: false });
      } else {
        toast.error(response.data.message || 'Failed to scrape page');
      }
    } catch (error) {
      console.error('Error scraping single page:', error);
      toast.error('Failed to scrape page');
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <ArrowPathIcon className="h-5 w-5 animate-spin text-blue-600" />;
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

  const formatDuration = (startTime, endTime = null) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
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
          <h1 className="text-2xl font-bold text-gray-900">Scraper</h1>
          <p className="text-gray-600">
            Monitor and control web scraping operations across your projects.
          </p>
        </div>
        <button
          onClick={() => setShowSinglePageModal(true)}
          className="btn-primary flex items-center"
        >
          <CpuChipIcon className="h-5 w-5 mr-2" />
          Scrape Single Page
        </button>
      </div>

      {/* Active Jobs */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Active Scraping Jobs</h3>
          <p className="text-sm text-gray-600">Currently running and recent scraping operations</p>
        </div>

        {scrapingJobs.length > 0 ? (
          <div className="space-y-4">
            {scrapingJobs.map((job) => (
              <div key={job.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getStatusIcon(job.status)}
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {job.website_name}
                      </h4>
                      <p className="text-sm text-gray-600">{job.website_url}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <span className={`badge ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                    
                    {job.status === 'running' ? (
                      <button
                        onClick={() => handleStopScraping(job.website_id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Stop Scraping"
                      >
                        <StopIcon className="h-5 w-5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStartScraping(job.website_id)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Start Scraping"
                      >
                        <PlayIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>Progress: {job.pages_scraped} / {job.total_pages} pages</span>
                    <span>{Math.round((job.pages_scraped / job.total_pages) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(job.pages_scraped / job.total_pages) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Job Stats */}
                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Started:</span>
                    <span className="ml-2 text-gray-900">
                      {new Date(job.started_at).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <span className="ml-2 text-gray-900">
                      {formatDuration(job.started_at, job.completed_at)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Last Activity:</span>
                    <span className="ml-2 text-gray-900">
                      {job.last_activity ? new Date(job.last_activity).toLocaleTimeString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <CpuChipIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No active scraping jobs</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start scraping websites from your projects to see activity here.
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <PlayIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Quick Start</h3>
              <p className="text-sm text-gray-600">Start scraping all configured websites</p>
            </div>
          </div>
          <button className="btn-primary mt-4 w-full">
            Start All
          </button>
        </div>

        <div className="card">
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Schedule Jobs</h3>
              <p className="text-sm text-gray-600">Set up automated scraping schedules</p>
            </div>
          </div>
          <button className="btn-secondary mt-4 w-full">
            Schedule
          </button>
        </div>

        <div className="card">
          <div className="flex items-center">
            <GlobeAltIcon className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Test Scraping</h3>
              <p className="text-sm text-gray-600">Test configurations on sample pages</p>
            </div>
          </div>
          <button
            onClick={() => setShowSinglePageModal(true)}
            className="btn-secondary mt-4 w-full"
          >
            Test Page
          </button>
        </div>
      </div>

      {/* Single Page Scraping Modal */}
      {showSinglePageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Scrape Single Page</h3>
              <p className="text-sm text-gray-600 mt-1">
                Test scraping on a specific URL
              </p>
            </div>
            
            <form onSubmit={handleSinglePageScraping} className="p-6 space-y-4">
              {/* URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL *
                </label>
                <input
                  type="url"
                  value={singlePageForm.url}
                  onChange={(e) => setSinglePageForm({...singlePageForm, url: e.target.value})}
                  className="input-field"
                  placeholder="https://example.com/page"
                  required
                />
              </div>

              {/* Use Selenium */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={singlePageForm.use_selenium}
                    onChange={(e) => setSinglePageForm({...singlePageForm, use_selenium: e.target.checked})}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Use Selenium (for JavaScript-heavy sites)
                  </span>
                </label>
              </div>

              {/* Form Actions */}
              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowSinglePageModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Scrape Page
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Scraper;