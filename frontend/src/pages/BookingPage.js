import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { ArrowLeft, Calendar as CalendarIcon, Clock, Check } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { format, addDays, startOfDay } from 'date-fns';
import { uk } from 'date-fns/locale';
import { validateUkrainianPhone, formatPhoneForDisplay } from '../utils/phoneValidator';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function BookingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [masters, setMasters] = useState([]);
  const [timeSlots, setTimeSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    service_id: '',
    service_name: '',
    master_id: '',
    master_name: '',
    date: '',
    time: '',
    client_name: '',
    client_phone: '',
    client_email: '',
    telegram_id: '',
    reminder_hours: 24,
    notes: ''
  });

  useEffect(() => {
    fetchServices();
    fetchMasters();
  }, []);

  useEffect(() => {
    if (formData.service_id && formData.date) {
      fetchTimeSlots();
    }
  }, [formData.service_id, formData.date]);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      toast.error('Помилка завантаження послуг');
    }
  };

  const fetchMasters = async () => {
    try {
      const response = await axios.get(`${API}/masters`);
      // Фільтруємо тільки активних майстрів
      setMasters(response.data.filter(m => m.is_active));
    } catch (error) {
      console.error('Помилка завантаження майстрів:', error);
      // Якщо не вдалось завантажити - використовуємо admin за замовчуванням
      setMasters([{ id: 'admin', name: 'Майстер', is_active: true }]);
    }
  };

  const fetchTimeSlots = async () => {
    try {
      const response = await axios.get(`${API}/timeslots/${formData.date}?service_id=${formData.service_id}&master_id=admin`);
      setTimeSlots(response.data);
    } catch (error) {
      toast.error('Помилка завантаження доступного часу');
    }
  };

  const handleServiceSelect = (service) => {
    setFormData({ ...formData, service_id: service.id, service_name: service.name });
    setStep(2);
  };

  const handleDateSelect = (date) => {
    setFormData({ ...formData, date });
    setStep(3);
  };

  const handleTimeSelect = (time) => {
    setFormData({ ...formData, time });
    setStep(4);
  };

  const handlePhoneChange = (e) => {
    let value = e.target.value;
    
    // Автоматично додаємо +380 якщо користувач почав вводити
    if (value.length === 1 && value !== '+') {
      value = '+380' + value;
    }
    
    setFormData({ ...formData, client_phone: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Валідація телефону
    if (!validateUkrainianPhone(formData.client_phone)) {
      toast.error('Невірний формат телефону. Використовуйте формат: +380XXXXXXXXX');
      return;
    }
    
    setLoading(true);
    
    try {
      const bookingData = {
        master_id: 'admin',  // Тимчасово використовуємо admin як майстра
        service_id: formData.service_id,
        date: formData.date,
        time: formData.time,
        client_name: formData.client_name,
        client_phone: formData.client_phone,
        client_email: formData.client_email || undefined,
        telegram_id: formData.telegram_id || undefined,
        reminder_hours: parseInt(formData.reminder_hours),
        notes: formData.notes || undefined
      };
      
      await axios.post(`${API}/bookings`, bookingData);
      toast.success('Запис успішно створено!', {
        description: 'Ми зв\'яжемося з вами для підтвердження'
      });
      setTimeout(() => navigate('/'), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при створенні запису');
    } finally {
      setLoading(false);
    }
  };

  const getNextDays = (count) => {
    const days = [];
    for (let i = 0; i < count; i++) {
      days.push(addDays(startOfDay(new Date()), i));
    }
    return days;
  };

  const selectedService = services.find(s => s.id === formData.service_id);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB] py-12 px-6">
      <div className="noise-overlay"></div>
      
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <Button 
            onClick={() => step === 1 ? navigate('/') : setStep(step - 1)} 
            variant="ghost" 
            className="mb-6 hover:bg-[#F3EBEB]"
            data-testid="back-button"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Назад
          </Button>
          <h1 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Онлайн-запис
          </h1>
          <p className="text-gray-600 mt-2">Крок {step} з 4</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div 
                key={i} 
                className={`h-2 flex-1 rounded-full transition-all ${
                  i <= step ? 'bg-[#D4A5A5]' : 'bg-rose-200/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-3xl p-8 lg:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-rose-200/50">
          {/* Step 1: Service Selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть послугу</h2>
                <p className="text-gray-600">Що вас цікавить?</p>
              </div>
              <div className="grid gap-4">
                {services.map((service) => (
                  <button
                    key={service.id}
                    onClick={() => handleServiceSelect(service)}
                    className="text-left p-6 border-2 border-rose-200/50 rounded-2xl hover:border-[#D4A5A5] hover:shadow-lg transition-all active:scale-98 group"
                    data-testid={`service-option-${service.id}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="space-y-2 flex-1">
                        <h3 className="text-xl font-semibold group-hover:text-[#D4A5A5] transition-colors">{service.name}</h3>
                        <p className="text-sm text-gray-600">{service.description}</p>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {service.duration_minutes} хв
                          </span>
                          <span className="text-lg font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                            {service.price} ₴
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Date Selection */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть дату</h2>
                <p className="text-gray-600">Коли вам зручно?</p>
              </div>
              
              {/* Розділення дат по місяцях */}
              {(() => {
                const days = getNextDays(180);
                const monthsMap = new Map();
                
                // Групуємо дати по місяцях
                days.forEach(day => {
                  const monthKey = format(day, 'yyyy-MM');
                  if (!monthsMap.has(monthKey)) {
                    monthsMap.set(monthKey, []);
                  }
                  monthsMap.get(monthKey).push(day);
                });
                
                return Array.from(monthsMap.entries()).map(([monthKey, monthDays]) => (
                  <div key={monthKey} className="space-y-4">
                    {/* Заголовок місяця */}
                    <div className="flex items-center gap-4">
                      <div className="flex-1 h-px bg-rose-200"></div>
                      <h3 className="text-xl font-semibold text-[#9E829C]" style={{ fontFamily: 'Playfair Display, serif' }}>
                        {format(monthDays[0], 'LLLL yyyy', { locale: uk })}
                      </h3>
                      <div className="flex-1 h-px bg-rose-200"></div>
                    </div>
                    
                    {/* Дати місяця */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {monthDays.map((day) => {
                        const dateStr = format(day, 'yyyy-MM-dd');
                        const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
                        return (
                          <button
                            key={dateStr}
                            onClick={() => handleDateSelect(dateStr)}
                            className="p-6 border-2 border-rose-200/50 rounded-2xl hover:border-[#D4A5A5] hover:shadow-lg transition-all active:scale-98 text-center group"
                            data-testid={`date-option-${dateStr}`}
                          >
                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">
                              {format(day, 'EEEE', { locale: uk })}
                            </div>
                            <div className="text-2xl font-bold group-hover:text-[#D4A5A5] transition-colors" style={{ fontFamily: 'Playfair Display, serif' }}>
                              {format(day, 'd')}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {format(day, 'MMMM', { locale: uk })}
                            </div>
                            {isToday && (
                              <div className="text-xs text-[#D4A5A5] font-semibold mt-2">Сьогодні</div>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ));
              })()}
            </div>
          )}

          {/* Step 3: Time Selection */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть час</h2>
                <p className="text-gray-600">Доступні слоти на {formData.date}</p>
              </div>
              {timeSlots.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">На цю дату немає доступних слотів</p>
                  <Button 
                    onClick={() => setStep(2)} 
                    className="mt-4 bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                  >
                    Обрати іншу дату
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
                  {timeSlots.map((slot) => (
                    <button
                      key={slot.time}
                      onClick={() => slot.available && handleTimeSelect(slot.time)}
                      disabled={!slot.available}
                      className={`p-4 rounded-xl font-medium transition-all ${
                        slot.available
                          ? 'border-2 border-rose-200/50 hover:border-[#D4A5A5] hover:shadow-lg active:scale-95 hover:bg-[#F3EBEB]'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                      data-testid={`time-slot-${slot.time}`}
                    >
                      {slot.time}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4: Contact Details */}
          {step === 4 && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Ваші контакти</h2>
                <p className="text-gray-600">Ми зв'яжемося з вами для підтвердження</p>
              </div>

              {/* Booking Summary */}
              <div className="bg-[#F3EBEB] p-6 rounded-2xl space-y-2">
                <h3 className="font-semibold text-lg mb-3" style={{ fontFamily: 'Playfair Display, serif' }}>Деталі запису</h3>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Послуга:</span>
                  <span className="font-medium">{formData.service_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Дата:</span>
                  <span className="font-medium">{formData.date}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Час:</span>
                  <span className="font-medium">{formData.time}</span>
                </div>
                {selectedService && (
                  <div className="flex justify-between text-sm pt-2 border-t border-rose-200/50">
                    <span className="text-gray-600">Вартість:</span>
                    <span className="font-bold text-lg text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {selectedService.price} ₴
                    </span>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="client_name">Ім'я *</Label>
                  <Input
                    id="client_name"
                    required
                    value={formData.client_name}
                    onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                    placeholder="Ваше ім'я"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300"
                    data-testid="input-client-name"
                  />
                </div>
                <div>
                  <Label htmlFor="client_phone">Телефон *</Label>
                  <Input
                    id="client_phone"
                    required
                    value={formData.client_phone}
                    onChange={handlePhoneChange}
                    placeholder="+380 XX XXX XX XX"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300"
                    data-testid="input-client-phone"
                  />
                  <p className="text-xs text-gray-500 mt-1">Формат: +380XXXXXXXXX</p>
                </div>
                <div>
                  <Label htmlFor="client_email">Email (опціонально)</Label>
                  <Input
                    id="client_email"
                    type="email"
                    value={formData.client_email}
                    onChange={(e) => setFormData({ ...formData, client_email: e.target.value })}
                    placeholder="your@email.com"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300"
                    data-testid="input-client-email"
                  />
                </div>
                <div>
                  <Label htmlFor="telegram_id">Telegram ID (опціонально)</Label>
                  <Input
                    id="telegram_id"
                    value={formData.telegram_id}
                    onChange={(e) => setFormData({ ...formData, telegram_id: e.target.value })}
                    placeholder="@username або chat_id"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300"
                    data-testid="input-telegram-id"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    📱 Нагадування приходитимуть по SMS на ваш номер телефону<br/>
                    💬 Telegram - додатково, якщо бажаєте дублювати в месенджер
                  </p>
                </div>
                <div>
                  <Label htmlFor="reminder_hours">Нагадати за</Label>
                  <select
                    id="reminder_hours"
                    value={formData.reminder_hours}
                    onChange={(e) => setFormData({ ...formData, reminder_hours: e.target.value })}
                    className="mt-1 w-full p-2 border border-rose-200/50 rounded-lg focus:ring-2 focus:ring-rose-300"
                    data-testid="select-reminder-hours"
                  >
                    <option value="1">1 годину</option>
                    <option value="2">2 години</option>
                    <option value="3">3 години</option>
                    <option value="6">6 годин</option>
                    <option value="12">12 годин</option>
                    <option value="24">24 години (1 день)</option>
                    <option value="48">48 годин (2 дні)</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="notes">Побажання (опціонально)</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Є особливі побажання?"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300 min-h-24"
                    data-testid="input-notes"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-6 rounded-full text-lg shadow-lg hover:shadow-xl active:scale-95 transition-all"
                data-testid="submit-booking-button"
              >
                {loading ? 'Створення запису...' : (
                  <>
                    <Check className="mr-2 h-5 w-5" />
                    Підтвердити запис
                  </>
                )}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default BookingPage;