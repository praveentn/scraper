// frontend/src/pages/Content.jsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentTextIcon,
  ClockIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';
import { contentAPI, projectsAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Content = () => {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project');
  
  const [snippets, setSnippets] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || '');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [selectedSnippet, setSelectedSnippet] = useState(null);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [ruleForm, setRuleForm] = useState({
    project_id: selectedProject,
    name: '',
    rule_type: 'css',
    selector: '',
    attribute: 'text',
    description: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadSnippets();
  }, [selectedProject, statusFilter, searchTerm]);

  const loadData = async () => {
    try {
      // Load projects
      const projectsResponse = await projectsAPI.getAll({ per_page: 100 });
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.projects);
      }
      
      loadSnippets();
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    }
  };

  const loadSnippets = async (page = 1) => {
    try {
      setLoading(true);
      const params = {
        page,
        per_page: 20,
        project_id: selectedProject || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchTerm || undefined
      };

      const response = await contentAPI.getSnippets(params);
      
      if (response.data.success) {
        setSnippets(response.data.snippets);
        setPagination(response.data.pagination);
      } else {
        // Mock data for demonstration
        setSnippets([
          {
            id: 1,
            content: "Advanced Machine Learning Techniques for Data Analysis",
            status: 'pending',
            confidence_score: 0.87,
            page_url: 'https://example.com/ml-guide',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            context: "<h1>Advanced Machine Learning Techniques for Data Analysis</h1><p>Explore cutting-edge ML algorithms..."
          },
          {
            id: 2,
            content: "The Future of Web Development: Trends and Technologies",
            status: 'approved',
            confidence_score: 0.92,
            page_url: 'https://example.com/web-trends',
            created_at: new Date(Date.now() - 172800000).toISOString(),
            context: "<h2>The Future of Web Development: Trends and Technologies</h2><p>As we look ahead..."
          },
          {
            id: 3,
            content: "Essential JavaScript Patterns Every Developer Should Know",
            status: 'pending',
            confidence_score: 0.75,
            page_url: 'https://example.com/js-patterns',
            created_at: new Date(Date.now() - 259200000).toISOString(),
            context: "<h3>Essential JavaScript Patterns Every Developer Should Know</h3><div>JavaScript patterns..."
          }
        ]);
        setPagination({ page: 1, pages: 1, total: 3, has_next: false, has_prev: false });
      }
    } catch (error) {
      console.error('Error loading snippets:', error);
      toast.error('Failed to load content snippets');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveSnippet = async (snippetId, status, notes = '') => {
    try {
      const response = await contentAPI.approveSnippet(snippetId, {
        status,
        review_notes: notes
      });
      
      if (response.data.success) {
        toast.success(`Snippet ${status} successfully`);
        loadSnippets(pagination.page);
        setSelectedSnippet(null);
      } else {
        toast.error(`Failed to ${status} snippet`);
      }
    } catch (error) {
      console.error(`Error ${status} snippet:`, error);
      toast.error(`Failed to ${status} snippet`);
    }
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    
    if (!ruleForm.name || !ruleForm.selector) {
      toast.error('Name and selector are required');
      return;
    }

    try {
      const response = await contentAPI.createRule(ruleForm);
      
      if (response.data.success) {
        toast.success('Extraction rule created successfully');
        setShowRuleModal(false);
        setRuleForm({
          project_id: selectedProject,
          name: '',
          rule_type: 'css',
          selector: '',
          attribute: 'text',
          description: ''
        });
      } else {
        toast.error(response.data.message || 'Failed to create rule');
      }
    } catch (error) {
      console.error('Error creating rule:', error);
      toast.error('Failed to create rule');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Content Review</h1>
          <p className="text-gray-600">
            Review and approve extracted content snippets from your scraped pages.
          </p>
        </div>
        <button
          onClick={() => setShowRuleModal(true)}
          className="btn-primary flex items-center"
        >
          <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
          Add Extraction Rule
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          {/* Project Filter */}
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="input-field w-48"
          >
            <option value="">All Projects</option>
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search content..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10 w-64"
            />
          </div>
        </div>

        <div className="text-sm text-gray-600">
          {pagination.total} snippet{pagination.total !== 1 ? 's' : ''} total
        </div>
      </div>

      {/* Content List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="large" />
        </div>
      ) : snippets.length > 0 ? (
        <>
          <div className="space-y-4">
            {snippets.map((snippet) => (
              <div key={snippet.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`badge ${getStatusColor(snippet.status)}`}>
                        {snippet.status}
                      </span>
                      {snippet.confidence_score && (
                        <span className={`text-sm font-medium ${getConfidenceColor(snippet.confidence_score)}`}>
                          {Math.round(snippet.confidence_score * 100)}% confidence
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(snippet.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <h3 className="text-lg font-medium text-gray-900 mb-2 line-clamp-2">
                      {snippet.content}
                    </h3>
                    
                    <p className="text-sm text-gray-600 mb-2">
                      Source: <a
                        href={snippet.page_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-500"
                      >
                        {snippet.page_url}
                      </a>
                    </p>
                    
                    {snippet.context && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs font-medium text-gray-700 mb-1">Context:</p>
                        <div 
                          className="text-xs text-gray-600 font-mono"
                          dangerouslySetInnerHTML={{ __html: snippet.context.substring(0, 200) + '...' }}
                        />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => setSelectedSnippet(snippet)}
                      className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>
                    
                    {snippet.status === 'pending' && (
                      <>
                        <button
                          onClick={() => handleApproveSnippet(snippet.id, 'approved')}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Approve"
                        >
                          <CheckCircleIcon className="h-5 w-5" />
                        </button>
                        
                        <button
                          onClick={() => handleApproveSnippet(snippet.id, 'rejected')}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Reject"
                        >
                          <XCircleIcon className="h-5 w-5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between">
              <button
                onClick={() => loadSnippets(pagination.page - 1)}
                disabled={!pagination.has_prev}
                className="btn-secondary disabled:opacity-50"
              >
                Previous
              </button>
              
              <span className="text-sm text-gray-600">
                Page {pagination.page} of {pagination.pages}
              </span>
              
              <button
                onClick={() => loadSnippets(pagination.page + 1)}
                disabled={!pagination.has_next}
                className="btn-secondary disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No content snippets found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || statusFilter !== 'all' || selectedProject
              ? 'Try adjusting your search or filter criteria.'
              : 'Start scraping websites to extract content snippets.'
            }
          </p>
        </div>
      )}

      {/* Snippet Detail Modal */}
      {selectedSnippet && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Content Snippet Details</h3>
                <button
                  onClick={() => setSelectedSnippet(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Content</h4>
                <p className="text-gray-900">{selectedSnippet.content}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Source URL</h4>
                <a
                  href={selectedSnippet.page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-500"
                >
                  {selectedSnippet.page_url}
                </a>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">HTML Context</h4>
                <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
                  <code className="text-sm font-mono text-gray-800">
                    {selectedSnippet.context}
                  </code>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
                  <span className={`badge ${getStatusColor(selectedSnippet.status)}`}>
                    {selectedSnippet.status}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Confidence</h4>
                  <span className={`font-medium ${getConfidenceColor(selectedSnippet.confidence_score)}`}>
                    {Math.round(selectedSnippet.confidence_score * 100)}%
                  </span>
                </div>
              </div>
              
              {selectedSnippet.status === 'pending' && (
                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleApproveSnippet(selectedSnippet.id, 'rejected')}
                    className="btn-danger"
                  >
                    <XCircleIcon className="h-4 w-4 mr-2" />
                    Reject
                  </button>
                  <button
                    onClick={() => handleApproveSnippet(selectedSnippet.id, 'approved')}
                    className="btn-success"
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-2" />
                    Approve
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add Rule Modal */}
      {showRuleModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Add Extraction Rule</h3>
            </div>
            
            <form onSubmit={handleCreateRule} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project *
                  </label>
                  <select
                    value={ruleForm.project_id}
                    onChange={(e) => setRuleForm({...ruleForm, project_id: e.target.value})}
                    className="input-field"
                    required
                  >
                    <option value="">Select project</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rule Type
                  </label>
                  <select
                    value={ruleForm.rule_type}
                    onChange={(e) => setRuleForm({...ruleForm, rule_type: e.target.value})}
                    className="input-field"
                  >
                    <option value="css">CSS Selector</option>
                    <option value="xpath">XPath</option>
                    <option value="regex">Regular Expression</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rule Name *
                </label>
                <input
                  type="text"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({...ruleForm, name: e.target.value})}
                  className="input-field"
                  placeholder="e.g., Page Titles"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Selector/Pattern *
                </label>
                <input
                  type="text"
                  value={ruleForm.selector}
                  onChange={(e) => setRuleForm({...ruleForm, selector: e.target.value})}
                  className="input-field"
                  placeholder={ruleForm.rule_type === 'css' ? 'h1, h2, h3' : ruleForm.rule_type === 'xpath' ? '//h1' : '\\b[A-Z][a-z]+\\b'}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Attribute
                </label>
                <select
                  value={ruleForm.attribute}
                  onChange={(e) => setRuleForm({...ruleForm, attribute: e.target.value})}
                  className="input-field"
                >
                  <option value="text">Text Content</option>
                  <option value="href">Link URL</option>
                  <option value="src">Image/Media Source</option>
                  <option value="html">HTML Content</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={ruleForm.description}
                  onChange={(e) => setRuleForm({...ruleForm, description: e.target.value})}
                  className="input-field resize-none"
                  rows={3}
                  placeholder="Optional description of what this rule extracts"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  Create Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Content;