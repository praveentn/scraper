// frontend/src/components/SqlExecutor.jsx
import React, { useState, useRef, useEffect } from 'react';
import {
  PlayIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { adminAPI } from '../utils/api';
import toast from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';

const SqlExecutor = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 100 });
  const [isDangerous, setIsDangerous] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    // Load query history from localStorage
    const savedHistory = localStorage.getItem('sql_history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const saveToHistory = (query, success) => {
    const historyItem = {
      id: Date.now(),
      query: query.trim(),
      timestamp: new Date().toISOString(),
      success
    };
    
    const newHistory = [historyItem, ...history.slice(0, 19)]; // Keep last 20
    setHistory(newHistory);
    localStorage.setItem('sql_history', JSON.stringify(newHistory));
  };

  const checkDangerousQuery = (sql) => {
    const dangerous = ['drop', 'delete', 'truncate', 'alter', 'insert', 'update'];
    const sqlLower = sql.toLowerCase().trim();
    return dangerous.some(keyword => sqlLower.includes(keyword));
  };

  const executeQuery = async (confirmDangerous = false) => {
    if (!query.trim()) {
      toast.error('Please enter a SQL query');
      return;
    }

    const dangerous = checkDangerousQuery(query);
    setIsDangerous(dangerous);

    if (dangerous && !confirmDangerous) {
      setShowConfirm(true);
      return;
    }

    setLoading(true);
    setResults(null);
    setShowConfirm(false);

    try {
      const requestData = {
        sql: query.trim(),
        page: pagination.page,
        per_page: pagination.per_page,
        confirm_dangerous: dangerous
      };

      const response = await adminAPI.executeSQL(requestData);

      if (response.data.success) {
        setResults(response.data);
        saveToHistory(query, true);
        toast.success('Query executed successfully');
      } else {
        toast.error(response.data.message || 'Query execution failed');
        saveToHistory(query, false);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Query execution failed';
      toast.error(errorMessage);
      saveToHistory(query, false);
      console.error('SQL execution error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQueryFromHistory = (historyQuery) => {
    setQuery(historyQuery);
    textareaRef.current?.focus();
  };

  const clearQuery = () => {
    setQuery('');
    setResults(null);
    textareaRef.current?.focus();
  };

  const formatValue = (value) => {
    if (value === null) return <span className="text-gray-400 italic">NULL</span>;
    if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
    if (typeof value === 'string' && value.length > 100) {
      return (
        <span title={value}>
          {value.substring(0, 100)}...
        </span>
      );
    }
    return String(value);
  };

  const copyQuery = () => {
    navigator.clipboard.writeText(query);
    toast.success('Query copied to clipboard');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">SQL Executor</h3>
            <p className="text-sm text-gray-600 mt-1">
              Execute raw SQL queries with full CRUD, DDL, and DML support
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <InformationCircleIcon className="h-5 w-5 text-blue-500" />
            <span className="text-sm text-gray-600">Database: scraper.db</span>
          </div>
        </div>

        {/* Query Input */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="border-b border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => executeQuery()}
                  disabled={loading || !query.trim()}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    loading || !query.trim()
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {loading ? (
                    <LoadingSpinner />
                  ) : (
                    <PlayIcon className="h-4 w-4" />
                  )}
                  <span>{loading ? 'Executing...' : 'Execute'}</span>
                </button>

                <button
                  onClick={clearQuery}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
                  title="Clear Query"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>

                <button
                  onClick={copyQuery}
                  disabled={!query.trim()}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg disabled:opacity-50"
                  title="Copy Query"
                >
                  <DocumentDuplicateIcon className="h-4 w-4" />
                </button>
              </div>

              <div className="text-sm text-gray-500">
                Lines: {query.split('\n').length} | Characters: {query.length}
              </div>
            </div>
          </div>

          <div className="p-4">
            <textarea
              ref={textareaRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your SQL query here... (e.g., SELECT * FROM users LIMIT 10)"
              className="w-full h-40 p-3 border border-gray-200 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              style={{ fontFamily: 'Menlo, Monaco, Consolas, monospace' }}
            />
          </div>

          {/* Pagination Controls for SELECT queries */}
          {query.toLowerCase().trim().startsWith('select') && (
            <div className="border-t border-gray-200 px-4 py-3">
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">Results per page:</label>
                <select
                  value={pagination.per_page}
                  onChange={(e) => setPagination({...pagination, per_page: parseInt(e.target.value)})}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                  <option value={500}>500</option>
                </select>
                
                <label className="text-sm font-medium text-gray-700">Page:</label>
                <input
                  type="number"
                  min="1"
                  value={pagination.page}
                  onChange={(e) => setPagination({...pagination, page: parseInt(e.target.value) || 1})}
                  className="w-20 text-sm border border-gray-300 rounded px-2 py-1"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dangerous Query Confirmation */}
      {showConfirm && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-yellow-800">Potentially Dangerous Operation</h4>
              <p className="text-sm text-yellow-700 mt-1">
                This query appears to modify data. Please confirm you want to proceed.
              </p>
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={() => executeQuery(true)}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm font-medium"
                >
                  Execute Anyway
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-1 rounded text-sm font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="mb-6">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="border-b border-gray-200 px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  <span className="font-medium text-gray-900">Query Results</span>
                </div>
                
                {results.pagination && (
                  <div className="text-sm text-gray-600">
                    Page {results.pagination.page} of {results.pagination.pages} 
                    ({results.pagination.total} total rows)
                  </div>
                )}
                
                {results.rowcount !== undefined && (
                  <div className="text-sm text-gray-600">
                    {results.rowcount} rows affected
                  </div>
                )}
              </div>
            </div>

            <div className="overflow-auto max-h-96">
              {results.rows && results.rows.length > 0 ? (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      {results.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50">
                        {results.columns.map((column, colIndex) => (
                          <td
                            key={colIndex}
                            className="px-4 py-3 text-sm text-gray-900 border-r border-gray-200 last:border-r-0 max-w-xs"
                          >
                            {formatValue(row[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  {results.message || 'Query executed successfully with no results'}
                </div>
              )}
            </div>

            {/* Pagination for results */}
            {results.pagination && results.pagination.pages > 1 && (
              <div className="border-t border-gray-200 px-4 py-3">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => {
                      setPagination({...pagination, page: results.pagination.page - 1});
                      executeQuery();
                    }}
                    disabled={!results.pagination.has_prev}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Previous
                  </button>
                  
                  <span className="text-sm text-gray-600">
                    Page {results.pagination.page} of {results.pagination.pages}
                  </span>
                  
                  <button
                    onClick={() => {
                      setPagination({...pagination, page: results.pagination.page + 1});
                      executeQuery();
                    }}
                    disabled={!results.pagination.has_next}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Query History */}
      {history.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="border-b border-gray-200 px-4 py-3">
            <h4 className="font-medium text-gray-900">Query History</h4>
          </div>
          <div className="max-h-64 overflow-auto">
            {history.map((item) => (
              <div
                key={item.id}
                className="px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                onClick={() => loadQueryFromHistory(item.query)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-gray-900 truncate">
                      {item.query}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      {item.success ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SqlExecutor;