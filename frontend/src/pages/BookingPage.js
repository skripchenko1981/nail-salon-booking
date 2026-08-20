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
  const [telegramLink, setTelegramLink] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [pendingTime, setPendingTime] = useState(null);
  
  const [formData, setFormData] = useState({
    service_id: '',
    service_name: '',
    master_id: '',
    master_name: '',
    date: '',
    time: '',
    client_name: '',
    client_surname: '',
    client_phone: '',
    client_email: '',
    reminder_hours: 2,
    notes: ''
  });

  const [groupedServices, setGroupedServices] = useState({});
  const [categoryLabels, setCategoryLabels] = useState({
    manicure: 'Манікюр',
    pedicure: 'Педикюр',
    podology: 'Подологія'
  });
  const [activeCategory, setActiveCategory] = useState('manicure');

  useEffect(() => {
    fetchServices();
    fetchMasters();
  }, []);

  useEffect(() => {
    if (formData.date && formData.service_id && formData.master_id) {
      fetchTimeSlots();
    }
  }, [formData.date, formData.service_id, formData.master_id]);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services/grouped`);
      setGroupedServices(response.data.services);
      setCategoryLabels(response.data.categories);
      setActiveCategory(Object.keys(response.data.categories)[0] || 'manicure');
      setServices(Object.values(response.data.services).flat());
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
      const response = await axios.get(`${API}/timeslots/${formData.date}?service_id=${formData.service_id}&master_id=${formData.master_id}`);
      setTimeSlots(response.data);
    } catch (error) {
      toast.error('Помилка завантаження доступного часу');
    }
  };

  const fetchMasterServices = async (masterId) => {
    try {
      const response = await axios.get(`${API}/services/grouped?master_id=${masterId}`);
      setGroupedServices(response.data.services);
      setCategoryLabels(response.data.categories);
      setActiveCategory(Object.keys(response.data.categories)[0] || 'manicure');
      setServices(Object.values(response.data.services).flat());
    } catch (error) {
      toast.error('Помилка завантаження послуг майстра');
    }
  };

  const handleMasterSelect = (master) => {
    setFormData({
      ...formData,
      master_id: master.id,
      master_name: master.name,
      service_id: '',  // Скидаємо обрану послугу
      service_name: ''
    });
    setStep(2);
    // Завантажити послуги цього майстра
    fetchMasterServices(master.id);
  };

  const handleServiceSelect = (service) => {
    setFormData({
      ...formData,
      service_id: service.id,
      service_name: service.name,
      duration_minutes: service.duration_minutes,
      price: service.price
    });
    setStep(3);
  };

  const handleDateSelect = (date) => {
    setFormData({ ...formData, date });
    setStep(4);
  };

  // Функція для перевірки чи час потребує попередження
  const isSpecialTime = (time) => {
    const specialTimes = ['08:00', '08:30', '18:00', '18:30', '19:00', '19:30', '20:00'];
    return specialTimes.includes(time);
  };

  const handleTimeSelect = (time) => {
    if (isSpecialTime(time)) {
      setPendingTime(time);
      setShowTimeWarning(true);
    } else {
      setFormData({ ...formData, time });
      setStep(5);
    }
  };

  const confirmTimeSelection = () => {
    setFormData({ ...formData, time: pendingTime });
    setShowTimeWarning(false);
    setPendingTime(null);
    setStep(5);
  };

  const cancelTimeSelection = () => {
    setShowTimeWarning(false);
    setPendingTime(null);
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
        master_id: formData.master_id,
        master_name: formData.master_name,
        service_id: formData.service_id,
        date: formData.date,
        time: formData.time,
        client_name: formData.client_name,
        client_surname: formData.client_surname,
        client_phone: formData.client_phone,
        client_email: formData.client_email || undefined,
        reminder_hours: parseInt(formData.reminder_hours),
        notes: formData.notes || undefined
      };
      
      const response = await axios.post(`${API}/bookings`, bookingData);
      
      // Зберегти посилання на Telegram
      if (response.data.telegram_subscription_link) {
        setTelegramLink(response.data.telegram_subscription_link);
        setShowSuccessModal(true);
      } else {
        toast.success('Запис успішно створено!', {
          description: 'Ми зв\'яжемося з вами для підтвердження'
        });
        setTimeout(() => navigate('/'), 2000);
      }
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
          <p className="text-gray-600 mt-2">Крок {step} з 5</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
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
          {/* Step 1: Master Selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть майстра</h2>
                <p className="text-gray-600">До кого б ви хотіли записатись?</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {masters.map((master) => (
                  <button
                    key={master.id}
                    onClick={() => handleMasterSelect(master)}
                    className="text-left p-6 border-2 border-rose-200/50 rounded-2xl hover:border-[#D4A5A5] hover:shadow-lg transition-all active:scale-98 group"
                    data-testid={`master-option-${master.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-full bg-[#F3EBEB] flex items-center justify-center">
                        {master.photo_url ? (
                          <img src={master.photo_url} alt={master.name} className="w-full h-full rounded-full object-cover" />
                        ) : (
                          <span className="text-2xl font-bold text-[#D4A5A5]">
                            {master.name.charAt(0)}
                          </span>
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold group-hover:text-[#D4A5A5] transition-colors">
                          {master.name}
                        </h3>
                        {master.bio && (
                          <p className="text-sm text-gray-600 mt-1">{master.bio}</p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Service Selection */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть послугу</h2>
                <p className="text-gray-600">Що вас цікавить?</p>
              </div>
              
              {/* Category Tabs */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {Object.entries(categoryLabels).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setActiveCategory(key)}
                    className={`px-6 py-3 rounded-full font-medium transition-all whitespace-nowrap ${
                      activeCategory === key
                        ? 'bg-[#D4A5A5] text-white shadow-lg'
                        : 'bg-white border-2 border-rose-200/50 text-gray-700 hover:border-[#D4A5A5]'
                    }`}
                    data-testid={`category-tab-${key}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              
              {/* Services in selected category */}
              <div className="grid gap-4">
                {(groupedServices[activeCategory] || []).length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>Немає послуг у цій категорії</p>
                  </div>
                ) : (
                  (groupedServices[activeCategory] || []).map((service) => (
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
                  ))
                )}
              </div>
            </div>
          )}

          {/* Step 3: Date Selection */}
          {step === 3 && (
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

          {/* Step 4: Time Selection */}
          {step === 4 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Оберіть час</h2>
                <p className="text-gray-600">Доступні слоти на {formData.date}</p>
              </div>
              {timeSlots.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">На цю дату немає доступних слотів</p>
                  <Button 
                    onClick={() => setStep(3)} 
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

          {/* Step 5: Client Information */}
          {step === 5 && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>Ваші контакти</h2>
                <p className="text-gray-600">Ми зв&apos;яжемося з вами для підтвердження</p>
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
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="client_name">Ім&apos;я *</Label>
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
                    <Label htmlFor="client_surname">Прізвище *</Label>
                    <Input
                      id="client_surname"
                      required
                      value={formData.client_surname}
                      onChange={(e) => setFormData({ ...formData, client_surname: e.target.value })}
                      placeholder="Ваше прізвище"
                      className="mt-1 border-rose-200/50 focus:ring-rose-300"
                      data-testid="input-client-surname"
                    />
                  </div>
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
                  <p className="text-xs text-gray-500 mt-1">
                    Після запису ви зможете підключити Telegram-нагадування (один раз)
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

      {/* Модальне вікно успішного бронювання */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl animate-in fade-in zoom-in duration-300">
            <div className="text-center">
              {/* Іконка успіху */}
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Check className="h-10 w-10 text-green-600" />
              </div>

              {/* Заголовок */}
              <h2 className="text-3xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
                Запис створено!
              </h2>
              
              <p className="text-gray-600 mb-6">
                Ваш запис очікує підтвердження майстра
              </p>

              {/* Telegram блок — ОБОВ'ЯЗКОВО */}
              {telegramLink && (
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 mb-6 border-2 border-blue-300 shadow-lg animate-pulse-once">
                  <div className="flex items-center justify-center mb-4">
                    <svg className="w-10 h-10 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.223-.548.223l.188-2.85 5.18-4.68c.223-.198-.054-.308-.346-.11l-6.4 4.03-2.76-.918c-.6-.187-.612-.6.125-.89l10.782-4.156c.5-.18.943.112.78.89z"/>
                    </svg>
                  </div>
                  
                  <h3 className="font-bold text-xl mb-2 text-gray-900">
                    Отримуйте нагадування в Telegram!
                  </h3>
                  <p className="text-sm text-gray-700 mb-1">
                    Натисніть кнопку нижче щоб підключити нагадування.
                  </p>
                  <p className="text-sm text-gray-700 mb-4">
                    <strong>Це потрібно зробити лише один раз</strong> — всі наступні записи отримуватимуть нагадування автоматично.
                  </p>
                  
                  <a
                    href={telegramLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl transition-colors text-lg text-center"
                    data-testid="telegram-subscribe-btn"
                  >
                    Підключити нагадування
                  </a>
                  
                  <p className="text-xs text-gray-500 mt-3 text-center">
                    Нагадування прийде за 2 години до вашого запису
                  </p>
                </div>
              )}

              {/* Кнопки */}
              <div className="space-y-3">
                <Button
                  onClick={() => {
                    setShowSuccessModal(false);
                    navigate('/');
                  }}
                  className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-3 rounded-xl"
                >
                  На головну
                </Button>
                
                <button
                  onClick={() => {
                    setShowSuccessModal(false);
                    navigate('/');
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                  Пропустити
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальне вікно попередження про спеціальний час */}
      {showTimeWarning && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl animate-in fade-in zoom-in duration-300">
            <div className="text-center">
              {/* Іконка попередження */}
              <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Clock className="h-10 w-10 text-amber-600" />
              </div>

              {/* Заголовок */}
              <h2 className="text-2xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
                Зверніть увагу
              </h2>
              
              <p className="text-gray-700 mb-6 leading-relaxed">
                Запис до 9:00 та на 18:00 і пізніше, можливий лише за попередньою домовленістю. В іншому випадку запис буде скасовано. Дякуємо за розуміння 🤍
              </p>

              <p className="text-sm text-gray-500 mb-6">
                Обраний час: <span className="font-semibold text-[#D4A5A5]">{pendingTime}</span>
              </p>

              {/* Кнопки */}
              <div className="space-y-3">
                <Button
                  onClick={confirmTimeSelection}
                  className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-3 rounded-xl"
                  data-testid="confirm-time-warning"
                >
                  Зрозуміло, продовжити
                </Button>
                
                <button
                  onClick={cancelTimeSelection}
                  className="w-full text-sm text-gray-500 hover:text-gray-700 underline py-2"
                  data-testid="cancel-time-warning"
                >
                  Обрати інший час
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BookingPage;