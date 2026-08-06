import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { SettingsProvider } from './context/SettingsContext';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import BookingPage from './pages/BookingPage';
import MyBookingsPage from './pages/MyBookingsPage';
import PortfolioPage from './pages/PortfolioPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminDashboard from './pages/AdminDashboard';
import MasterLoginPage from './pages/MasterLoginPage';
import MasterDashboard from './pages/MasterDashboard';
import './App.css';

function ProtectedRoute({ role, children }) {
  const { isAuthenticated, role: userRole } = useAuth();
  if (!isAuthenticated || userRole !== role) {
    return <Navigate to={`/${role}/login`} replace />;
  }
  return children;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <SettingsProvider>
          <ThemeProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/booking" element={<BookingPage />} />
                <Route path="/my-bookings" element={<MyBookingsPage />} />
                <Route path="/portfolio" element={<PortfolioPage />} />
                <Route path="/admin/login" element={<AdminLoginPage />} />
                <Route path="/admin/*" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
                <Route path="/master/login" element={<MasterLoginPage />} />
                <Route path="/master/*" element={<ProtectedRoute role="master"><MasterDashboard /></ProtectedRoute>} />
              </Routes>
            </BrowserRouter>
            <Toaster />
          </ThemeProvider>
        </SettingsProvider>
      </AuthProvider>
    </div>
  );
}

export default App;