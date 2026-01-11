import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { LayoutDashboard, Calendar, Settings, Package, LogOut, Menu, X, Users, Image } from 'lucide-react';
import AdminOverview from '../components/admin/AdminOverview';
import AdminBookings from '../components/admin/AdminBookings';
import AdminServices from '../components/admin/AdminServices';
import AdminSchedule from '../components/admin/AdminSchedule';
import AdminClients from '../components/admin/AdminClients';
import AdminSettings from '../components/admin/AdminSettings';
import AdminVacations from '../components/admin/AdminVacations';
import AdminMasters from '../components/admin/AdminMasters';
import AdminGallery from '../components/admin/AdminGallery';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const token = localStorage.getItem('admin_token');
  const [isAdmin, setIsAdmin] = useState(true);

  // Protect admin routes
  useEffect(() => {
    if (!token) {
      navigate('/admin/login');
    }
  }, [token, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
    navigate('/admin/login');
  };

  // Адмін бачить все
  const menuItems = [
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Огляд', testId: 'nav-dashboard' },
    { path: '/admin/bookings', icon: Calendar, label: 'Записи', testId: 'nav-bookings' },
    { path: '/admin/clients', icon: Users, label: 'Клієнти', testId: 'nav-clients' },
    { path: '/admin/masters', icon: Users, label: 'Майстри', testId: 'nav-masters' },
    { path: '/admin/services', icon: Package, label: 'Послуги', testId: 'nav-services' },
    { path: '/admin/schedule', icon: Settings, label: 'Розклад', testId: 'nav-schedule' },
    { path: '/admin/vacations', icon: Calendar, label: 'Відпустки', testId: 'nav-vacations' },
    { path: '/admin/gallery', icon: Image, label: 'Галерея', testId: 'nav-gallery' },
    { path: '/admin/settings', icon: Settings, label: 'Налаштування', testId: 'nav-settings' },
  ];

  if (!token) return null;

  return (
    <div className="min-h-screen bg-[#FDFCFB] flex">
      <div className="noise-overlay"></div>
      
      {/* Mobile Menu Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 bg-white p-2 rounded-lg shadow-lg border border-rose-200/50"
        data-testid="mobile-menu-button"
      >
        {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-white border-r border-rose-200/50
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b border-rose-200/50">
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
              Nail Studio
            </h1>
            <p className="text-sm text-gray-500 mt-1">Админ-панель</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    setSidebarOpen(false);
                  }}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                    ${isActive 
                      ? 'bg-[#F3EBEB] text-[#D4A5A5] font-medium' 
                      : 'text-gray-600 hover:bg-[#FDFCFB] hover:text-[#D4A5A5]'
                    }
                  `}
                  data-testid={item.testId}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-rose-200/50">
            <Button
              onClick={handleLogout}
              variant="ghost"
              className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
              data-testid="logout-button"
            >
              <LogOut className="mr-3 h-5 w-5" />
              Вийти
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-12">
          <Routes>
            <Route path="/" element={<Navigate to="/admin/masters" replace />} />
            <Route path="/dashboard" element={<AdminOverview />} />
            <Route path="/bookings" element={<AdminBookings />} />
            <Route path="/clients" element={<AdminClients />} />
            <Route path="/services" element={<AdminServices />} />
            <Route path="/schedule" element={<AdminSchedule />} />
            <Route path="/masters" element={<AdminMasters />} />
            <Route path="/vacations" element={<AdminVacations />} />
            <Route path="/gallery" element={<AdminGallery />} />
            <Route path="/settings" element={<AdminSettings />} />
          </Routes>
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/20 z-30" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

export default AdminDashboard;