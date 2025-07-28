// frontend/src/pages/Login.jsx
import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../utils/auth';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Login = () => {
  const { login, register, isAuthenticated, loading } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    confirmPassword: ''
  });

  useEffect(() => {
    // Clear form when switching modes
    setFormData({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      confirmPassword: ''
    });
  }, [isLoginMode]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (isLoginMode) {
        const result = await login({
          email: formData.email,
          password: formData.password
        });
        
        if (result.success) {
          // Redirect handled by auth context
        }
      } else {
        // Registration validation
        if (formData.password !== formData.confirmPassword) {
          toast.error('Passwords do not match');
          return;
        }

        if (formData.password.length < 8) {
          toast.error('Password must be at least 8 characters');
          return;
        }

        const result = await register({
          email: formData.email,
          password: formData.password,
          first_name: formData.first_name,
          last_name: formData.last_name
        });

        if (result.success) {
          setIsLoginMode(true);
          setFormData({
            email: formData.email, // Keep email for login
            password: '',
            first_name: '',
            last_name: '',
            confirmPassword: ''
          });
        }
      }
    } catch (error) {
      console.error('Authentication error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-lg bg-blue-600">
            <span className="text-xl font-bold text-white">B</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            {isLoginMode ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enterprise Web Scraping Platform
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {!isLoginMode && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                    First name
                  </label>
                  <input
                    id="first_name"
                    name="first_name"
                    type="text"
                    required={!isLoginMode}
                    value={formData.first_name}
                    onChange={handleInputChange}
                    className="input-field mt-1"
                    placeholder="First name"
                  />
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                    Last name
                  </label>
                  <input
                    id="last_name"
                    name="last_name"
                    type="text"
                    required={!isLoginMode}
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className="input-field mt-1"
                    placeholder="Last name"
                  />
                </div>
              </div>
            )}
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="input-field mt-1"
                placeholder="Email address"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isLoginMode ? 'current-password' : 'new-password'}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="input-field pr-10"
                  placeholder="Password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            {!isLoginMode && (
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required={!isLoginMode}
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className="input-field mt-1"
                  placeholder="Confirm password"
                />
              </div>
            )}
          </div>

          <div>
            <button
              type="submit"
              disabled={submitting}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <LoadingSpinner size="small" />
              ) : (
                isLoginMode ? 'Sign in' : 'Create account'
              )}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLoginMode(!isLoginMode)}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              {isLoginMode 
                ? "Don't have an account? Sign up" 
                : 'Already have an account? Sign in'
              }
            </button>
          </div>
        </form>

        {/* Demo credentials */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Demo Credentials</h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p>Admin: admin@example.com / admin123</p>
            <p>User: user@example.com / user123</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;