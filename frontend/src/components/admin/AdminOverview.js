import React, { useEffect, useState } from 'react';
import { Calendar, Clock, DollarSign, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import api from '../../lib/api';
import { toast } from 'sonner';

function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [mastersStats, setMastersStats] = useState([]);
  const [masters, setMasters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMaster, setSelectedMaster] = useState('all');

  useEffect(() => {
    fetchStats();
    fetchMonthlyStats();
    fetchMastersStats();
    fetchMasters();
  }, [selectedYear, selectedMaster]);

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/stats');
      setStats(response.data);
    } catch (error) {
      toast.error('Помилка завантаження статистики');
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyStats = async () => {
    try {
      const params = { year: selectedYear };
      if (selectedMaster !== 'all') {
        params.master_id = selectedMaster;
      }
      const response = await api.get('/admin/stats/monthly', { params });
      setMonthlyStats(response.data);
    } catch (error) {
      console.error('Помилка завантаження місячної статистики');
    }
  };

  const fetchMastersStats = async () => {
    try {
      const response = await api.get('/admin/stats/masters');
      setMastersStats(response.data);
    } catch (error) {
      console.error('Помилка завантаження статистики майстрів');
    }
  };

  const fetchMasters = async () => {
    try {
      const response = await api.get('/masters');
      setMasters(response.data);
    } catch (error) {
      console.error('Помилка завантаження списку майстрів');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  const statCards = [
    {
      title: 'Всього записів',
      value: stats?.total_bookings || 0,
      icon: Calendar,
      color: 'bg-blue-100 text-blue-600',
      testId: 'stat-total-bookings'
    },
    {
      title: 'Сьогодні',
      value: stats?.today_bookings || 0,
      icon: Clock,
      color: 'bg-purple-100 text-purple-600',
      testId: 'stat-today-bookings'
    },
    {
      title: 'Очікують підтвердження',
      value: stats?.pending_bookings || 0,
      icon: AlertCircle,
      color: 'bg-yellow-100 text-yellow-600',
      testId: 'stat-pending-bookings'
    },
    {
      title: 'Підтверджено',
      value: stats?.confirmed_bookings || 0,
      icon: CheckCircle,
      color: 'bg-green-100 text-green-600',
      testId: 'stat-confirmed-bookings'
    },
    {
      title: 'Завершено',
      value: stats?.completed_bookings || 0,
      icon: CheckCircle,
      color: 'bg-teal-100 text-teal-600',
      testId: 'stat-completed-bookings'
    },
    {
      title: 'Скасовано',
      value: stats?.cancelled_bookings || 0,
      icon: XCircle,
      color: 'bg-red-100 text-red-600',
      testId: 'stat-cancelled-bookings'
    },
    {
      title: 'Загальна виручка',
      value: `${stats?.total_revenue || 0} ₴`,
      icon: DollarSign,
      color: 'bg-[#F3EBEB] text-[#D4A5A5]',
      testId: 'stat-total-revenue'
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
          Огляд
        </h1>
        <p className="text-gray-600 mt-2">Статистика та ключові показники</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div 
              key={card.title} 
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all"
              data-testid={card.testId}
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`${card.color} p-3 rounded-xl`}>
                  <Icon className="h-6 w-6" />
                </div>
              </div>
              <p className="text-gray-600 text-sm mb-1">{card.title}</p>
              <p className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                {card.value}
              </p>
            </div>
          );
        })}
      </div>

      {/* Quick Info */}
      <div className="bg-gradient-to-r from-[#F3EBEB] to-[#FDFCFB] rounded-2xl p-8 border border-rose-200/50">
        <h2 className="text-2xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
          Ласкаво просимо до адмін-панелі!
        </h2>
        <p className="text-gray-600">
          Тут ви можете керувати майстрами, налаштовувати сайт та переглядати загальну статистику.
        </p>
      </div>

      {/* Статистика по майстрам */}
      <div className="bg-white rounded-2xl p-8 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)]">
        <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: 'Playfair Display, serif' }}>
          Статистика по майстрам
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mastersStats.map((master) => (
            <div 
              key={master.master_id}
              className="p-6 rounded-xl border-2 border-rose-200/50 hover:border-[#D4A5A5] transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-lg">{master.master_name}</h3>
                  <p className="text-sm text-gray-500">{master.master_email}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  master.is_active 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {master.is_active ? 'Активний' : 'Неактивний'}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-rose-100">
                  <span className="text-gray-600 text-sm">Всього записів:</span>
                  <span className="font-bold text-[#D4A5A5]">{master.total_bookings}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 text-sm">Підтверджено:</span>
                  <span className="font-semibold text-green-600">{master.confirmed}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 text-sm">Завершено:</span>
                  <span className="font-semibold text-blue-600">{master.completed}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 text-sm">Скасовано:</span>
                  <span className="font-semibold text-red-600">{master.cancelled}</span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-rose-200/50">
                  <span className="text-gray-700 font-medium">Виручка:</span>
                  <span className="font-bold text-lg text-[#D4A5A5]">{master.revenue} ₴</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {mastersStats.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Немає майстрів для відображення статистики
          </div>
        )}
      </div>

      {/* Місячна аналітика */}
      <div className="bg-white rounded-2xl p-8 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-2xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
            Аналіз діяльності по місяцях
          </h2>
          <div className="flex flex-col sm:flex-row gap-2">
            <select 
              value={selectedMaster}
              onChange={(e) => setSelectedMaster(e.target.value)}
              className="px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#D4A5A5]"
            >
              <option value="all">Всі майстри (сукупно)</option>
              {masters.map((master) => (
                <option key={master.id} value={master.id}>
                  {master.name}
                </option>
              ))}
            </select>
            <select 
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#D4A5A5]"
            >
              {[...Array(5)].map((_, i) => {
                const year = new Date().getFullYear() - i;
                return <option key={year} value={year}>{year}</option>;
              })}
            </select>
          </div>
        </div>

        {selectedMaster !== 'all' && (
          <div className="mb-4 p-3 bg-[#F3EBEB]/50 rounded-lg border border-rose-200/50">
            <p className="text-sm text-gray-700">
              📊 Показано статистику для: <span className="font-semibold">
                {masters.find(m => m.id === selectedMaster)?.name || 'Майстер'}
              </span>
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {monthlyStats.map((month, index) => (
            <div 
              key={index}
              className={`p-6 rounded-xl border-2 transition-all cursor-pointer ${
                selectedMonth === index 
                  ? 'border-[#D4A5A5] bg-[#F3EBEB]/30' 
                  : 'border-rose-200/50 hover:border-[#D4A5A5]/50'
              }`}
              onClick={() => setSelectedMonth(index)}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-bold text-lg">{month.month_name}</h3>
                <span className="text-2xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {month.total_bookings}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Підтверджено:</span>
                  <span className="font-semibold text-green-600">{month.confirmed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Завершено:</span>
                  <span className="font-semibold text-blue-600">{month.completed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Скасовано:</span>
                  <span className="font-semibold text-red-600">{month.cancelled}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-rose-200/50">
                  <span className="text-gray-600 font-medium">Виручка:</span>
                  <span className="font-bold text-[#D4A5A5]">{month.revenue} ₴</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {monthlyStats.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Немає даних за {selectedYear} рік
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminOverview;