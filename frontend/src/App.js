import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { SettingsProvider } from './context/SettingsContext';
import { ThemeProvider } from './context/ThemeContext';
import HomePage from './pages/HomePage';
import BookingPage from './pages/BookingPage';
import MyBookingsPage from './pages/MyBookingsPage';
import PortfolioPage from './pages/PortfolioPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminDashboard from './pages/AdminDashboard';
import MasterLoginPage from './pages/MasterLoginPage';
import MasterDashboard from './pages/MasterDashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <SettingsProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/booking" element={<BookingPage />} />
              <Route path="/my-bookings" element={<MyBookingsPage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              <Route path="/admin/login" element={<AdminLoginPage />} />
              <Route path="/admin/*" element={<AdminDashboard />} />
              <Route path="/master/login" element={<MasterLoginPage />} />
              <Route path="/master/*" element={<MasterDashboard />} />
            </Routes>
          </BrowserRouter>
          <Toaster />
        </ThemeProvider>
      </SettingsProvider>
    </div>
  );
}

export default App;