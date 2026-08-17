import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Clock, Save } from 'lucide-react';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';
import { Switch } from '../ui/switch';

function AdminSchedule() {
  const { user } = useAuth();
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  const getMasterId = () => user?.id || 'admin';

  const daysOfWeek = [
    'Понеділок',
    'Вівторок',
    'Середа',
    'Четвер',
    "П'ятниця",
    'Субота',
    'Неділя'
  ];

  useEffect(() => {
    fetchSchedule();
  }, []);

  const fetchSchedule = async () => {
    try {
      const masterId = getMasterId();
      const response = await api.get(`/schedule?master_id=${masterId}`);
      setSchedule(response.data);
    } catch (error) {
      toast.error('Помилка завантаження розкладу');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (daySchedule) => {
    const masterId = getMasterId();
    
    try {
      await api.post('/schedule', {
        master_id: masterId,
        day_of_week: daySchedule.day_of_week,
        start_time: daySchedule.start_time,
        end_time: daySchedule.end_time,
        is_working: daySchedule.is_working
      });
      toast.success('Розклад оновлено');
      fetchSchedule();
    } catch (error) {
      toast.error('Помилка при збереженні');
    }
  };

  const handleChange = (index, field, value) => {
    const newSchedule = [...schedule];
    newSchedule[index] = { ...newSchedule[index], [field]: value };
    setSchedule(newSchedule);
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
          Розклад роботи
        </h1>
        <p className="text-gray-600 mt-2">Налаштуйте робочі години для кожного дня тижня</p>
      </div>

      <div className="space-y-4">
        {schedule.map((daySchedule, index) => (
          <div 
            key={daySchedule.day_of_week} 
            className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)]"
            data-testid={`schedule-day-${daySchedule.day_of_week}`}
          >
            <div className="flex flex-col lg:flex-row lg:items-center gap-6">
              <div className="lg:w-48">
                <h3 className="text-lg font-semibold">{daysOfWeek[daySchedule.day_of_week]}</h3>
              </div>

              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={daySchedule.is_working}
                    onCheckedChange={(checked) => handleChange(index, 'is_working', checked)}
                    data-testid={`schedule-working-${daySchedule.day_of_week}`}
                  />
                  <span className="text-sm text-gray-600">
                    {daySchedule.is_working ? 'Робочий день' : 'Вихідний'}
                  </span>
                </div>

                {daySchedule.is_working && (
                  <div className="flex items-center gap-4 flex-1">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-[#D4A5A5]" />
                      <Input
                        type="time"
                        value={daySchedule.start_time}
                        onChange={(e) => handleChange(index, 'start_time', e.target.value)}
                        className="w-32"
                        data-testid={`schedule-start-${daySchedule.day_of_week}`}
                      />
                    </div>
                    <span className="text-gray-400">—</span>
                    <div className="flex items-center gap-2">
                      <Input
                        type="time"
                        value={daySchedule.end_time}
                        onChange={(e) => handleChange(index, 'end_time', e.target.value)}
                        className="w-32"
                        data-testid={`schedule-end-${daySchedule.day_of_week}`}
                      />
                    </div>
                  </div>
                )}
              </div>

              <Button 
                onClick={() => handleSave(daySchedule)} 
                className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white lg:w-auto"
                data-testid={`schedule-save-${daySchedule.day_of_week}`}
              >
                <Save className="h-4 w-4 mr-2" />
                Зберегти
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gradient-to-r from-[#F3EBEB] to-[#FDFCFB] rounded-2xl p-6 border border-rose-200/50">
        <h3 className="font-semibold mb-2">💡 Підказка</h3>
        <p className="text-sm text-gray-600">
          Розклад визначає, в які дні та години клієнти можуть записуватися на послуги. 
          Вимкніть перемикач для вихідних днів.
        </p>
      </div>
    </div>
  );
}

export default AdminSchedule;
