import React, { useEffect, useState } from 'react';
import { Calendar, Clock, DollarSign, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки статистики');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Загрузка...</div>;
  }

  const statCards = [
    {
      title: 'Всего записей',
      value: stats?.total_bookings || 0,
      icon: Calendar,
      color: 'bg-blue-100 text-blue-600',
      testId: 'stat-total-bookings'
    },
    {
      title: 'Сегодня',
      value: stats?.today_bookings || 0,
      icon: Clock,
      color: 'bg-purple-100 text-purple-600',
      testId: 'stat-today-bookings'
    },
    {
      title: 'Ожидают подтверждения',
      value: stats?.pending_bookings || 0,
      icon: AlertCircle,
      color: 'bg-yellow-100 text-yellow-600',
      testId: 'stat-pending-bookings'
    },
    {
      title: 'Подтверждено',
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
      title: 'Отменено',
      value: stats?.cancelled_bookings || 0,
      icon: XCircle,
      color: 'bg-red-100 text-red-600',
      testId: 'stat-cancelled-bookings'
    },
    {
      title: 'Общая выручка',
      value: `${stats?.total_revenue || 0} ₽`,
      icon: DollarSign,
      color: 'bg-[#F3EBEB] text-[#D4A5A5]',
      testId: 'stat-total-revenue'
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
          Обзор
        </h1>
        <p className="text-gray-600 mt-2">Статистика и ключевые показатели</p>
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
          Добро пожаловать в админ-панель!
        </h2>
        <p className="text-gray-600">
          Здесь вы можете управлять записями, услугами, расписанием и просматривать статистику.
          Используйте меню слева для навигации.
        </p>
      </div>
    </div>
  );
}

export default AdminOverview;