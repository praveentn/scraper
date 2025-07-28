// frontend/src/components/ProjectCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import {
  FolderIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';

const ProjectCard = ({ project, onDelete }) => {
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

  return (
    <div className="card hover:shadow-soft-lg transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <FolderIcon className="h-8 w-8 text-blue-500" />
          </div>
          <div className="min-w-0 flex-1">
            <Link to={`/projects/${project.id}`} className="block">
              <h3 className="text-lg font-medium text-gray-900 hover:text-blue-600 transition-colors">
                {project.name}
              </h3>
            </Link>
            {project.description && (
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {project.description}
              </p>
            )}
          </div>
        </div>

        <Menu as="div" className="relative flex-shrink-0">
          <Menu.Button className="p-1 rounded-lg hover:bg-gray-100 transition-colors">
            <EllipsisVerticalIcon className="h-5 w-5 text-gray-400" />
          </Menu.Button>
          
          <Transition
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <Menu.Item>
                {({ active }) => (
                  <Link
                    to={`/projects/${project.id}`}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } flex items-center px-4 py-2 text-sm text-gray-700`}
                  >
                    <EyeIcon className="mr-3 h-4 w-4" />
                    View Details
                  </Link>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <Link
                    to={`/projects/${project.id}/edit`}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } flex items-center px-4 py-2 text-sm text-gray-700`}
                  >
                    <PencilIcon className="mr-3 h-4 w-4" />
                    Edit Project
                  </Link>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={() => onDelete(project.id)}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } flex items-center w-full px-4 py-2 text-sm text-red-700`}
                  >
                    <TrashIcon className="mr-3 h-4 w-4" />
                    Delete Project
                  </button>
                )}
              </Menu.Item>
            </Menu.Items>
          </Transition>
        </Menu>
      </div>

      {/* Tags */}
      {project.tags && project.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {project.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
            >
              {tag}
            </span>
          ))}
          {project.tags.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              +{project.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="flex items-center justify-center">
            <GlobeAltIcon className="h-4 w-4 text-gray-400 mr-1" />
            <span className="text-sm font-medium text-gray-900">
              {project.websites_count || 0}
            </span>
          </div>
          <div className="text-xs text-gray-500">Websites</div>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center">
            <DocumentTextIcon className="h-4 w-4 text-gray-400 mr-1" />
            <span className="text-sm font-medium text-gray-900">
              {project.pages_scraped || 0}
            </span>
          </div>
          <div className="text-xs text-gray-500">Pages</div>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center">
            <span className="text-sm font-medium text-gray-900">
              {project.snippets_count || 0}
            </span>
          </div>
          <div className="text-xs text-gray-500">Snippets</div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`badge ${getStatusColor(project.status)}`}>
            {project.status}
          </span>
          {project.priority && (
            <span className={`badge ${getPriorityColor(project.priority)}`}>
              {project.priority}
            </span>
          )}
        </div>
        
        <div className="text-xs text-gray-500">
          {project.updated_at && (
            <>Updated {new Date(project.updated_at).toLocaleDateString()}</>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectCard;