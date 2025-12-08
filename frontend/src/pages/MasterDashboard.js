import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, NavLink } from 'react-router-dom';
import { LayoutDashboard, Calendar, Users, Package, Settings, LogOut, User } from 'lucide-react';
import { Button } from '../components/ui/button';
import AdminOverview from '../components/admin/AdminOverview';
import AdminBookings from '../components/admin/AdminBookings';
import AdminServices from '../components/admin/AdminServices';
import AdminSchedule from '../components/admin/AdminSchedule';
import AdminClients from '../components/admin/AdminClients';
import AdminVacations from '../components/admin/AdminVacations';

function MasterDashboard() {
  const navigate = useNavigate();
  const [masterName, setMasterName] = useState('Майстер');
  const [masterEmail, setMasterEmail] = useState('');
  
  useEffect(() => {
    // Отримати дані майстра з localStorage
    const masterData = JSON.parse(localStorage.getItem('master_data') || '{}');
    if (masterData.name) {
      setMasterName(masterData.name);
    }
    if (masterData.email) {
      setMasterEmail(masterData.email);
    }
  }, []);
  
  const handleLogout = () => {
    localStorage.removeItem('master_token');
    localStorage.removeItem('master_data');
    navigate('/master/login');
  };

  const menuItems = [
    { path: '/master/dashboard', icon: LayoutDashboard, label: 'Огляд', testId: 'nav-dashboard' },
    { path: '/master/bookings', icon: Calendar, label: 'Записи', testId: 'nav-bookings' },
    { path: '/master/clients', icon: Users, label: 'Клієнти', testId: 'nav-clients' },
    { path: '/master/services', icon: Package, label: 'Послуги', testId: 'nav-services' },
    { path: '/master/schedule', icon: Settings, label: 'Розклад', testId: 'nav-schedule' },
    { path: '/master/vacations', icon: Calendar, label: 'Відпустки', testId: 'nav-vacations' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FDFCFB] via-[#F3EBEB] to-[#FDFCFB]">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 min-h-screen bg-white border-r border-rose-200/50 sticky top-0">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
              Nail Studio
            </h1>
            <p className="text-sm text-gray-600 mt-1">Панель майстра</p>
          </div>

          {/* Master Info */}
          <div className="px-4 pb-4 mb-4 border-b border-rose-200/50">
            <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-[#F3EBEB] to-[#FDFCFB] rounded-xl">
              <div className="w-10 h-10 rounded-full bg-[#D4A5A5] flex items-center justify-center flex-shrink-0">
                <User className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate" title={masterName}>
                  {masterName}
                </p>
                <p className="text-xs text-gray-500 truncate" title={masterEmail}>
                  {masterEmail}
                </p>
              </div>
            </div>
          </div>

          <nav className="px-3">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all ${
                      isActive
                        ? 'bg-[#F3EBEB] text-[#D4A5A5] font-medium'
                        : 'text-gray-700 hover:bg-rose-50'
                    }`
                  }
                  data-testid={item.testId}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-rose-200/50 absolute bottom-0 w-64">
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
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <Routes>
            <Route path="/" element={<Navigate to="/master/dashboard" replace />} />
            <Route path="/dashboard" element={<AdminOverview />} />
            <Route path="/bookings" element={<AdminBookings />} />
            <Route path="/clients" element={<AdminClients />} />
            <Route path="/services" element={<AdminServices />} />
            <Route path="/schedule" element={<AdminSchedule />} />
            <Route path="/vacations" element={<AdminVacations />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default MasterDashboard;
