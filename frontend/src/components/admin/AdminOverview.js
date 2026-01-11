import React, { useEffect, useState } from 'react';
import { Calendar, Clock, DollarSign, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [mastersStats, setMastersStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchStats();
    fetchMonthlyStats();
  }, [selectedMonth, selectedYear]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error('Помилка завантаження статистики');
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyStats = async () => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      const response = await axios.get(`${API}/admin/stats/monthly`, {
        params: { year: selectedYear },
        headers: { Authorization: `Bearer ${token}` }
      });
      setMonthlyStats(response.data);
    } catch (error) {
      console.error('Помилка завантаження місячної статистики');
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
          Тут ви можете керувати записами, послугами, розкладом та переглядати статистику.
          Використовуйте меню зліва для навігації.
        </p>
      </div>

      {/* Місячна аналітика */}
      <div className="bg-white rounded-2xl p-8 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-2xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
            Аналіз діяльності по місяцях
          </h2>
          <div className="flex gap-2">
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