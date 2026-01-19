import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Calendar, Clock, Sparkles, Phone, Mail, MapPin } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function HomePage() {
  const navigate = useNavigate();
  const [services, setServices] = useState([]);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const serviceImages = [
    'https://images.pexels.com/photos/5128123/pexels-photo-5128123.jpeg',
    'https://images.unsplash.com/photo-1727199433272-70fdb94c8430',
    'https://customer-assets.emergentagent.com/job_beauty-hub-180/artifacts/htap3t0o_logo.jpg'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB]">
      <div className="noise-overlay"></div>
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-rose-200/50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>Nail Studio</h1>
          <div className="flex gap-4 items-center">
            <button 
              onClick={() => navigate('/my-bookings')} 
              className="text-sm hover:text-[#D4A5A5] transition-colors"
              data-testid="nav-my-bookings"
            >
              Мои записи
            </button>
            <button 
              onClick={() => navigate('/admin/login')} 
              className="text-xs text-gray-400 hover:text-[#9E829C] transition-colors"
              data-testid="nav-admin-login"
            >
              Админ
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-24 px-6">
        <div className="container mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-fade-in">
              <div className="space-y-4">
                <p className="text-xs uppercase tracking-widest text-[#9E829C] font-medium">Профессиональный уход</p>
                <h2 className="text-5xl lg:text-6xl font-bold tracking-tight leading-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                  Красота ваших
                  <span className="block text-[#D4A5A5]">рук и ног</span>
                </h2>
                <p className="text-lg text-gray-600 leading-relaxed max-w-xl">
                  Доверьте заботу о своих ногтях профессионалу. Качественный маникюр и педикюр в уютной атмосфере.
                </p>
              </div>
              <div className="flex gap-4">
                <Button 
                  onClick={() => navigate('/booking')} 
                  className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white px-8 py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
                  data-testid="hero-book-button"
                >
                  <Calendar className="mr-2 h-5 w-5" />
                  Записаться онлайн
                </Button>
              </div>
              <div className="flex gap-8 pt-4">
                <div>
                  <p className="text-3xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>500+</p>
                  <p className="text-sm text-gray-500">Довольных клиентов</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>3+</p>
                  <p className="text-sm text-gray-500">Года опыта</p>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_60px_rgb(0,0,0,0.08)] transition-all duration-500">
                <img 
                  src="https://customer-assets.emergentagent.com/job_beauty-hub-180/artifacts/htap3t0o_logo.jpg" 
                  alt="Маникюр" 
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-2xl shadow-xl border border-rose-200/50">
                <div className="flex items-center gap-3">
                  <div className="bg-[#F3EBEB] p-3 rounded-full">
                    <Sparkles className="h-6 w-6 text-[#D4A5A5]" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Качество гарантировано</p>
                    <p className="text-xs text-gray-500">Профессиональные материалы</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-24 px-6 bg-white">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16 space-y-4">
            <p className="text-xs uppercase tracking-widest text-[#9E829C] font-medium">Наши услуги</p>
            <h3 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
              Что мы предлагаем
            </h3>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <div 
                key={service.id} 
                className="group bg-[#FDFCFB] rounded-2xl overflow-hidden border border-rose-200/50 hover:shadow-[0_20px_60px_rgb(0,0,0,0.08)] transition-all duration-500 hover:-translate-y-2"
                data-testid={`service-card-${index}`}
              >
                <div className="aspect-[4/3] overflow-hidden">
                  <img 
                    src={service.image_url || serviceImages[index % serviceImages.length]} 
                    alt={service.name} 
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                  />
                </div>
                <div className="p-6 space-y-3">
                  <h4 className="text-2xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>{service.name}</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">{service.description}</p>
                  <div className="flex justify-between items-center pt-4 border-t border-rose-200/50">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Clock className="h-4 w-4" />
                      <span>{service.duration_minutes} мин</span>
                    </div>
                    <p className="text-2xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>{service.price} ₽</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-12">
            <Button 
              onClick={() => navigate('/booking')} 
              className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white px-8 py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
              data-testid="services-book-button"
            >
              Выбрать услугу и записаться
            </Button>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-24 px-6 bg-gradient-to-b from-white to-[#F3EBEB]">
        <div className="container mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="relative order-2 lg:order-1">
              <div className="aspect-[4/3] rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                <img 
                  src="https://images.unsplash.com/photo-1619596664171-1707d321835d" 
                  alt="Интерьер студии" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            <div className="space-y-6 order-1 lg:order-2">
              <p className="text-xs uppercase tracking-widest text-[#9E829C] font-medium">О нас</p>
              <h3 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                Мастер с душой
              </h3>
              <div className="space-y-4 text-gray-600 leading-relaxed">
                <p>
                  Добро пожаловать в нашу уютную студию! Я — профессиональный мастер маникюра и педикюра с более чем 3-летним опытом работы.
                </p>
                <p>
                  Использую только качественные материалы и современные техники. Каждый клиент для меня особенный, и я стремлюсь создать атмосферу комфорта и заботы.
                </p>
                <p>
                  Ваши руки и ногти заслуживают лучшего ухода. Доверьтесь профессионалу и наслаждайтесь результатом!
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-24 px-6 bg-[#FDFCFB]">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12 space-y-4">
            <p className="text-xs uppercase tracking-widest text-[#9E829C] font-medium">Контакты</p>
            <h3 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
              Свяжитесь с нами
            </h3>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl border border-rose-200/50 text-center space-y-3 hover:shadow-lg transition-all">
              <div className="bg-[#F3EBEB] w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                <Phone className="h-8 w-8 text-[#D4A5A5]" />
              </div>
              <p className="font-semibold">Телефон</p>
              <p className="text-gray-600">+7 (999) 123-45-67</p>
            </div>
            <div className="bg-white p-8 rounded-2xl border border-rose-200/50 text-center space-y-3 hover:shadow-lg transition-all">
              <div className="bg-[#F3EBEB] w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                <Mail className="h-8 w-8 text-[#D4A5A5]" />
              </div>
              <p className="font-semibold">Email</p>
              <p className="text-gray-600">info@nailstudio.ru</p>
            </div>
            <div className="bg-white p-8 rounded-2xl border border-rose-200/50 text-center space-y-3 hover:shadow-lg transition-all">
              <div className="bg-[#F3EBEB] w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                <MapPin className="h-8 w-8 text-[#D4A5A5]" />
              </div>
              <p className="font-semibold">Адрес</p>
              <p className="text-gray-600">Москва, ул. Примерная, 1</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-white border-t border-rose-200/50">
        <div className="container mx-auto max-w-7xl text-center">
          <p className="text-3xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>Nail Studio</p>
          <p className="text-gray-500 text-sm">© 2025 Все права защищены</p>
        </div>
      </footer>
    </div>
  );
}

export default HomePage;