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
import { ru } from 'date-fns/locale';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function BookingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [timeSlots, setTimeSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    service_id: '',
    service_name: '',
    date: '',
    time: '',
    client_name: '',
    client_phone: '',
    client_email: '',
    notes: ''
  });

  useEffect(() => {
    fetchServices();
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
      toast.error('Ошибка загрузки услуг');
    }
  };

  const fetchTimeSlots = async () => {
    try {
      const response = await axios.get(`${API}/timeslots/${formData.date}?service_id=${formData.service_id}`);
      setTimeSlots(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки доступного времени');
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const bookingData = {
        service_id: formData.service_id,
        date: formData.date,
        time: formData.time,
        client_name: formData.client_name,
        client_phone: formData.client_phone,
        client_email: formData.client_email || undefined,
        notes: formData.notes || undefined
      };
      
      await axios.post(`${API}/bookings`, bookingData);
      toast.success('Запись успешно создана!', {
        description: 'Мы свяжемся с вами для подтверждения'
      });
      setTimeout(() => navigate('/'), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при создании записи');
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
            Онлайн-запись
          </h1>
          <p className="text-gray-600 mt-2">Шаг {step} из 4</p>
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
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Выберите услугу</h2>
                <p className="text-gray-600">Что вас интересует?</p>
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
                            {service.duration_minutes} мин
                          </span>
                          <span className="text-lg font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                            {service.price} ₽
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
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Выберите дату</h2>
                <p className="text-gray-600">Когда вам удобно?</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {getNextDays(14).map((day) => {
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
                        {format(day, 'EEEE', { locale: ru })}
                      </div>
                      <div className="text-2xl font-bold group-hover:text-[#D4A5A5] transition-colors" style={{ fontFamily: 'Playfair Display, serif' }}>
                        {format(day, 'd')}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {format(day, 'MMMM', { locale: ru })}
                      </div>
                      {isToday && (
                        <div className="text-xs text-[#D4A5A5] font-semibold mt-2">Сегодня</div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Time Selection */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Выберите время</h2>
                <p className="text-gray-600">Доступные слоты на {formData.date}</p>
              </div>
              {timeSlots.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">На эту дату нет доступных слотов</p>
                  <Button 
                    onClick={() => setStep(2)} 
                    className="mt-4 bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                  >
                    Выбрать другую дату
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
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Ваши контакты</h2>
                <p className="text-gray-600">Мы свяжемся с вами для подтверждения</p>
              </div>

              {/* Booking Summary */}
              <div className="bg-[#F3EBEB] p-6 rounded-2xl space-y-2">
                <h3 className="font-semibold text-lg mb-3" style={{ fontFamily: 'Playfair Display, serif' }}>Детали записи</h3>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Услуга:</span>
                  <span className="font-medium">{formData.service_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Дата:</span>
                  <span className="font-medium">{formData.date}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Время:</span>
                  <span className="font-medium">{formData.time}</span>
                </div>
                {selectedService && (
                  <div className="flex justify-between text-sm pt-2 border-t border-rose-200/50">
                    <span className="text-gray-600">Стоимость:</span>
                    <span className="font-bold text-lg text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {selectedService.price} ₽
                    </span>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="client_name">Имя *</Label>
                  <Input
                    id="client_name"
                    required
                    value={formData.client_name}
                    onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                    placeholder="Ваше имя"
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
                    onChange={(e) => setFormData({ ...formData, client_phone: e.target.value })}
                    placeholder="+7 (999) 123-45-67"
                    className="mt-1 border-rose-200/50 focus:ring-rose-300"
                    data-testid="input-client-phone"
                  />
                </div>
                <div>
                  <Label htmlFor="client_email">Email (опционально)</Label>
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
                  <Label htmlFor="notes">Пожелания (опционально)</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Есть особые пожелания?"
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
                {loading ? 'Создание записи...' : (
                  <>
                    <Check className="mr-2 h-5 w-5" />
                    Подтвердить запись
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