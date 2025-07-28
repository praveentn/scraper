// frontend/src/pages/Projects.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  FolderIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EllipsisVerticalIcon
} from '@heroicons/react/24/outline';
import { projectsAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ProjectCard from '../components/ProjectCard';
import toast from 'react-hot-toast';

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  useEffect(() => {
    loadProjects();
  }, [searchTerm, statusFilter]);

  const loadProjects = async (page = 1) => {
    try {
      setLoading(true);
      const params = {
        page,
        per_page: 12,
        search: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined
      };

      const response = await projectsAPI.getAll(params);
      
      if (response.data.success) {
        setProjects(response.data.projects);
        setPagination(response.data.pagination);
      } else {
        toast.error('Failed to load projects');
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await projectsAPI.delete(projectId);
      
      if (response.data.success) {
        toast.success('Project deleted successfully');
        loadProjects(pagination.page);
      } else {
        toast.error('Failed to delete project');
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      toast.error('Failed to delete project');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600">
            Manage your web scraping projects and track their progress.
          </p>
        </div>
        <Link to="/projects/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          New Project
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative flex-1 sm:flex-none sm:w-64">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        <div className="text-sm text-gray-600">
          {pagination.total} project{pagination.total !== 1 ? 's' : ''} total
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="large" />
        </div>
      ) : projects.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={handleDeleteProject}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between">
              <button
                onClick={() => loadProjects(pagination.page - 1)}
                disabled={!pagination.has_prev}
                className="btn-secondary disabled:opacity-50"
              >
                Previous
              </button>
              
              <span className="text-sm text-gray-600">
                Page {pagination.page} of {pagination.pages}
              </span>
              
              <button
                onClick={() => loadProjects(pagination.page + 1)}
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
          <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No projects found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filter criteria.'
              : 'Get started by creating your first project.'
            }
          </p>
          {!searchTerm && statusFilter === 'all' && (
            <div className="mt-6">
              <Link to="/projects/new" className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Project
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Projects;