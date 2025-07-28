// frontend/src/pages/Reports.jsx
import React, { useState, useEffect } from 'react';
import {
  DocumentArrowDownIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  TrashIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { reportsAPI, projectsAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Reports = () => {
  const [exports, setExports] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [exportForm, setExportForm] = useState({
    export_type: 'csv',
    filters: {
      data_type: 'snippets',
      project_id: '',
      status: '',
      date_from: '',
      date_to: ''
    }
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
      
      // Load exports
      const exportsResponse = await reportsAPI.getExports();
      if (exportsResponse.data.success) {
        setExports(exportsResponse.data.exports);
      } else {
        // Mock data for demonstration
        setExports([
          {
            id: 1,
            export_type: 'csv',
            filename: 'content_snippets_20240128.csv',
            status: 'completed',
            progress: 100,
            file_size: 2048000,
            row_count: 1250,
            created_at: new Date(Date.now() - 3600000).toISOString(),
            completed_at: new Date(Date.now() - 3000000).toISOString(),
            filters: { data_type: 'snippets', status: 'approved' }
          },
          {
            id: 2,
            export_type: 'excel',
            filename: 'pages_export_20240127.xlsx',
            status: 'processing',
            progress: 65,
            created_at: new Date(Date.now() - 1800000).toISOString(),
            filters: { data_type: 'pages', project_id: '1' }
          },
          {
            id: 3,
            export_type: 'json',
            filename: 'project_data_20240126.json',
            status: 'failed',
            progress: 0,
            error_message: 'Database connection timeout',
            created_at: new Date(Date.now() - 7200000).toISOString(),
            filters: { data_type: 'snippets' }
          }
        ]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExport = async (e) => {
    e.preventDefault();
    
    try {
      const response = await reportsAPI.createExport({
        export_type: exportForm.export_type,
        filters: exportForm.filters
      });
      
      if (response.data.success) {
        toast.success('Export created successfully');
        setShowCreateModal(false);
        setExportForm({
          export_type: 'csv',
          filters: {
            data_type: 'snippets',
            project_id: '',
            status: '',
            date_from: '',
            date_to: ''
          }
        });
        loadData();
      } else {
        toast.error(response.data.message || 'Failed to create export');
      }
    } catch (error) {
      console.error('Error creating export:', error);
      toast.error('Failed to create export');
    }
  };

  const handleDownload = async (exportId, filename) => {
    try {
      const response = await reportsAPI.downloadExport(exportId);
      
      // Create blob and download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      
      toast.success('Export downloaded successfully');
    } catch (error) {
      console.error('Error downloading export:', error);
      toast.error('Failed to download export');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-blue-600 animate-pulse" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-600" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
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
          <h1 className="text-2xl font-bold text-gray-900">Reports & Exports</h1>
          <p className="text-gray-600">
            Generate and download reports from your scraped data and content.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Export
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <DocumentArrowDownIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {exports.filter(e => e.status === 'completed').length}
              </p>
              <p className="text-sm text-gray-600">Completed</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <ClockIcon className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {exports.filter(e => e.status === 'processing').length}
              </p>
              <p className="text-sm text-gray-600">Processing</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <XCircleIcon className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {exports.filter(e => e.status === 'failed').length}
              </p>
              <p className="text-sm text-gray-600">Failed</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {exports.reduce((sum, e) => sum + (e.row_count || 0), 0).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Total Records</p>
            </div>
          </div>
        </div>
      </div>

      {/* Exports List */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Recent Exports</h3>
          <p className="text-sm text-gray-600">Your export history and download links</p>
        </div>

        {exports.length > 0 ? (
          <div className="space-y-4">
            {exports.map((exportItem) => (
              <div key={exportItem.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getStatusIcon(exportItem.status)}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">
                        {exportItem.filename}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className={`badge ${getStatusColor(exportItem.status)}`}>
                          {exportItem.status}
                        </span>
                        <span className="text-xs text-gray-500 uppercase font-medium">
                          {exportItem.export_type}
                        </span>
                        {exportItem.row_count && (
                          <span className="text-xs text-gray-500">
                            {exportItem.row_count.toLocaleString()} records
                          </span>
                        )}
                        {exportItem.file_size && (
                          <span className="text-xs text-gray-500">
                            {formatFileSize(exportItem.file_size)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {exportItem.status === 'completed' && (
                      <button
                        onClick={() => handleDownload(exportItem.id, exportItem.filename)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Download"
                      >
                        <ArrowDownTrayIcon className="h-5 w-5" />
                      </button>
                    )}
                    
                    <button className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                      <EyeIcon className="h-5 w-5" />
                    </button>
                    
                    <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Progress bar for processing exports */}
                {exportItem.status === 'processing' && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                      <span>Processing...</span>
                      <span>{exportItem.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${exportItem.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Error message for failed exports */}
                {exportItem.status === 'failed' && exportItem.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800">
                      <strong>Error:</strong> {exportItem.error_message}
                    </p>
                  </div>
                )}

                {/* Export details */}
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Created:</span>
                    <span className="ml-2 text-gray-900">
                      {formatDate(exportItem.created_at)}
                    </span>
                  </div>
                  {exportItem.completed_at && (
                    <div>
                      <span className="text-gray-600">Completed:</span>
                      <span className="ml-2 text-gray-900">
                        {formatDate(exportItem.completed_at)}
                      </span>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-600">Data Type:</span>
                    <span className="ml-2 text-gray-900 capitalize">
                      {exportItem.filters?.data_type || 'Mixed'}
                    </span>
                  </div>
                  {exportItem.filters?.status && (
                    <div>
                      <span className="text-gray-600">Status Filter:</span>
                      <span className="ml-2 text-gray-900 capitalize">
                        {exportItem.filters.status}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No exports yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Create your first export to download your scraped data.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-primary"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Export
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Export Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Create Export</h3>
              <p className="text-sm text-gray-600 mt-1">
                Configure your data export settings
              </p>
            </div>
            
            <form onSubmit={handleCreateExport} className="p-6 space-y-6">
              {/* Export Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Export Format
                </label>
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { value: 'csv', label: 'CSV', description: 'Comma-separated values' },
                    { value: 'excel', label: 'Excel', description: 'XLSX spreadsheet' },
                    { value: 'json', label: 'JSON', description: 'JavaScript Object Notation' },
                    { value: 'pdf', label: 'PDF', description: 'Portable Document Format' }
                  ].map(type => (
                    <label key={type.value} className="cursor-pointer">
                      <input
                        type="radio"
                        name="export_type"
                        value={type.value}
                        checked={exportForm.export_type === type.value}
                        onChange={(e) => setExportForm({...exportForm, export_type: e.target.value})}
                        className="sr-only"
                      />
                      <div className={`p-3 border-2 rounded-lg text-center transition-colors ${
                        exportForm.export_type === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <div className="text-sm font-medium">{type.label}</div>
                        <div className="text-xs text-gray-500 mt-1">{type.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Data Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Type
                </label>
                <select
                  value={exportForm.filters.data_type}
                  onChange={(e) => setExportForm({
                    ...exportForm,
                    filters: { ...exportForm.filters, data_type: e.target.value }
                  })}
                  className="input-field"
                >
                  <option value="snippets">Content Snippets</option>
                  <option value="pages">Scraped Pages</option>
                  <option value="websites">Website Configurations</option>
                </select>
              </div>

              {/* Filters */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project
                  </label>
                  <select
                    value={exportForm.filters.project_id}
                    onChange={(e) => setExportForm({
                      ...exportForm,
                      filters: { ...exportForm.filters, project_id: e.target.value }
                    })}
                    className="input-field"
                  >
                    <option value="">All Projects</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>

                {exportForm.filters.data_type === 'snippets' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Status
                    </label>
                    <select
                      value={exportForm.filters.status}
                      onChange={(e) => setExportForm({
                        ...exportForm,
                        filters: { ...exportForm.filters, status: e.target.value }
                      })}
                      className="input-field"
                    >
                      <option value="">All Status</option>
                      <option value="approved">Approved</option>
                      <option value="pending">Pending</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Date
                  </label>
                  <input
                    type="date"
                    value={exportForm.filters.date_from}
                    onChange={(e) => setExportForm({
                      ...exportForm,
                      filters: { ...exportForm.filters, date_from: e.target.value }
                    })}
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    To Date
                  </label>
                  <input
                    type="date"
                    value={exportForm.filters.date_to}
                    onChange={(e) => setExportForm({
                      ...exportForm,
                      filters: { ...exportForm.filters, date_to: e.target.value }
                    })}
                    className="input-field"
                  />
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  Create Export
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;