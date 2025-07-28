// frontend/src/utils/auth.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app start
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      // Verify token is still valid
      authAPI.profile()
        .then(response => {
          if (response.data.success) {
            setUser(response.data.user);
          } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
          }
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      
      if (response.data.success) {
        const { user, tokens } = response.data;
        setUser(user);
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('user', JSON.stringify(user));
        toast.success('Login successful');
        return { success: true };
      } else {
        toast.error(response.data.message || 'Login failed');
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      toast.success('Logged out successfully');
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      
      if (response.data.success) {
        toast.success('Registration successful. Please log in.');
        return { success: true };
      } else {
        toast.error(response.data.message || 'Registration failed');
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const value = {
    user,
    login,
    logout,
    register,
    loading,
    isAuthenticated: !!user,
    isAdmin,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};