// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './utils/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects.jsx';
import CreateProject from './pages/CreateProject';
import ProjectDetail from './pages/ProjectDetail';
import Websites from './pages/Websites';
import Scraper from './pages/Scraper';
import Content from './pages/Content';
import Reports from './pages/Reports';
import Admin from './pages/Admin';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
          
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="projects" element={<Projects />} />
              <Route path="projects/new" element={<CreateProject />} />
              <Route path="projects/:id" element={<ProjectDetail />} />
              <Route path="websites" element={<Websites />} />
              <Route path="scraper" element={<Scraper />} />
              <Route path="content" element={<Content />} />
              <Route path="reports" element={<Reports />} />
              <Route path="admin" element={<Admin />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;