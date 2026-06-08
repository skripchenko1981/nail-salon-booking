import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Calendar, Clock, Sparkles, Phone, Mail, MapPin, Instagram, Facebook, User } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function HomePage() {
  const navigate = useNavigate();
  const { themeColors } = useTheme();
  const [masters, setMasters] = useState([]);
  const [selectedMaster, setSelectedMaster] = useState(null);
  const [services, setServices] = useState([]);
  const [groupedServices, setGroupedServices] = useState({});
  const [categoryLabels, setCategoryLabels] = useState({
    manicure: 'Манікюр',
    pedicure: 'Педикюр',
    podology: 'Подологія'
  });
  const [activeCategory, setActiveCategory] = useState('manicure');
  const [promoBlocks, setPromoBlocks] = useState([]);
  const [settings, setSettings] = useState({
    site_name: 'Nail Studio',
    about_text: '',
    phone: '',
    email: '',
    address: '',
    instagram: '',
    facebook: '',
    working_hours: '',
    hero_title: 'Ваша краса - наша пристрасть',
    hero_subtitle: 'Професійний манікюр та педикюр',
    hero_button_text: 'Записатися онлайн',
    services_title: 'Наші послуги',
    services_subtitle: 'Ми пропонуємо широкий спектр послуг',
    why_us_title: 'Чому обирають нас?',
    why_us_reason_1: 'Досвідчені майстри',
    why_us_reason_2: 'Якісні матеріали',
    why_us_reason_3: 'Стерильність та безпека'
  });

  useEffect(() => {
    fetchMasters();
    fetchSettings();
    fetchPromoBlocks();
  }, []);

  useEffect(() => {
    if (selectedMaster) {
      fetchMasterServices(selectedMaster.id);
    }
  }, [selectedMaster]);

  const fetchMasters = async () => {
    try {
      const response = await axios.get(`${API}/masters`);
      const activeMasters = response.data.filter(m => m.is_active);
      setMasters(activeMasters);
      if (activeMasters.length > 0) {
        setSelectedMaster(activeMasters[0]);
      }
    } catch (error) {
      console.error('Помилка завантаження майстрів:', error);
    }
  };

  const fetchMasterServices = async (masterId) => {
    try {
      const response = await axios.get(`${API}/services/grouped?master_id=${masterId}`);
      setGroupedServices(response.data.services);
      setCategoryLabels(response.data.categories);
      // Flatten for backward compatibility
      const allServices = Object.values(response.data.services).flat();
      setServices(allServices);
      // Set first non-empty category as active
      const firstNonEmpty = Object.entries(response.data.services).find(([_, services]) => services.length > 0);
      if (firstNonEmpty) {
        setActiveCategory(firstNonEmpty[0]);
      }
    } catch (error) {
      console.error('Помилка завантаження послуг:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Помилка завантаження налаштувань:', error);
    }
  };

  const fetchPromoBlocks = async () => {
    try {
      const response = await axios.get(`${API}/promo-blocks`);
      setPromoBlocks(response.data);
    } catch (error) {
      console.error('Помилка завантаження промо-блоків:', error);
    }
  };

  const serviceImages = [
    'https://images.pexels.com/photos/5128123/pexels-photo-5128123.jpeg',
    'https://images.unsplash.com/photo-1727199433272-70fdb94c8430',
    'https://hel1.your-objectstorage.com/bucket-cloud/uploads/logo/IMG_9032.PNG?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Checksum-Mode=ENABLED&X-Amz-Credential=5492XA7J7V9I783B3R8A%2F20260608%2Fhel1%2Fs3%2Faws4_request&X-Amz-Date=20260608T201317Z&X-Amz-Expires=600&X-Amz-SignedHeaders=host&x-id=GetObject&X-Amz-Signature=4b9938589ff90f5d358b755a9e29663d4424689dfdc9b89d696be40f49862a44'
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
              onClick={() => navigate('/portfolio')} 
              className="text-sm hover:text-[#D4A5A5] transition-colors"
            >
              Портфоліо
            </button>
            <button 
              onClick={() => navigate('/my-bookings')} 
              className="text-sm hover:text-[#D4A5A5] transition-colors"
              data-testid="nav-my-bookings"
            >
              Мої записи
            </button>
            <button 
              onClick={() => navigate('/master/login')} 
              className="text-sm hover:text-[#D4A5A5] transition-colors"
              data-testid="nav-master-login"
            >
              Вхід для майстра
            </button>
            <button 
              onClick={() => navigate('/admin/login')} 
              className="text-xs text-gray-400 hover:text-[#9E829C] transition-colors"
              data-testid="nav-admin-login"
            >
              Адмін
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
                <p className="text-xs uppercase tracking-widest font-medium" style={{ color: themeColors.secondary }}>Професійний догляд</p>
                <h2 className="text-5xl lg:text-6xl font-bold tracking-tight leading-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {settings.hero_title || 'Ваша краса - наша пристрасть'}
                </h2>
                <p className="text-lg text-gray-600 leading-relaxed max-w-xl">
                  {settings.hero_subtitle || 'Професійний манікюр та педикюр у затишній атмосфері'}
                </p>
              </div>
              <div className="flex gap-4">
                <Button 
                  onClick={() => navigate('/booking')} 
                  className="text-white px-8 py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
                  style={{ backgroundColor: themeColors.primary }}
                  data-testid="hero-book-button"
                >
                  <Calendar className="mr-2 h-5 w-5" />
                  {settings.hero_button_text || 'Записатися онлайн'}
                </Button>
              </div>
              <div className="flex gap-8 pt-4">
                <div>
                  <p className="text-3xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>500+</p>
                  <p className="text-sm text-gray-500">Задоволених клієнтів</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>3+</p>
                  <p className="text-sm text-gray-500">Роки досвіду</p>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_60px_rgb(0,0,0,0.08)] transition-all duration-500">
                <img 
                  src="https://hel1.your-objectstorage.com/bucket-cloud/uploads/logo/IMG_9032.PNG?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Checksum-Mode=ENABLED&X-Amz-Credential=5492XA7J7V9I783B3R8A%2F20260608%2Fhel1%2Fs3%2Faws4_request&X-Amz-Date=20260608T201317Z&X-Amz-Expires=600&X-Amz-SignedHeaders=host&x-id=GetObject&X-Amz-Signature=4b9938589ff90f5d358b755a9e29663d4424689dfdc9b89d696be40f49862a44" 
                  alt="Манікюр" 
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-2xl shadow-xl border border-rose-200/50">
                <div className="flex items-center gap-3">
                  <div className="bg-[#F3EBEB] p-3 rounded-full">
                    <Sparkles className="h-6 w-6 text-[#D4A5A5]" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Якість гарантовано</p>
                    <p className="text-xs text-gray-500">Професійні матеріали</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Promo Blocks Section */}
      {promoBlocks.length > 0 && (
        <section className="py-16 px-6">
          <div className="container mx-auto max-w-7xl">
            <div className="grid gap-8">
              {promoBlocks.map((block) => (
                <div 
                  key={block.id}
                  className="bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_60px_rgb(0,0,0,0.08)] transition-all duration-500"
                >
                  <div className="flex flex-col md:flex-row">
                    {block.image_url && (
                      <div className="md:w-1/3">
                        <img 
                          src={block.image_url} 
                          alt={block.title}
                          className="w-full h-64 md:h-full object-cover"
                        />
                      </div>
                    )}
                    <div className={`${block.image_url ? 'md:w-2/3' : 'w-full'} p-8 md:p-12 flex flex-col justify-center`}>
                      <h3 className="text-3xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif', color: themeColors.primary }}>
                        {block.title}
                      </h3>
                      <p className="text-gray-600 text-lg mb-6 leading-relaxed">
                        {block.description}
                      </p>
                      {block.button_text && block.button_link && (
                        <div>
                          <Button
                            onClick={() => navigate(block.button_link)}
                            className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white px-8 py-6 text-lg"
                          >
                            {block.button_text}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Services Section */}
      <section className="py-24 px-6 bg-white">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-12 space-y-4">
            <p className="text-xs uppercase tracking-widest font-medium" style={{ color: themeColors.secondary }}>ПОСЛУГИ</p>
            <h3 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
              {settings.services_title || 'Наші послуги'}
            </h3>
            {settings.services_subtitle && (
              <p className="text-gray-600 max-w-2xl mx-auto">
                {settings.services_subtitle}
              </p>
            )}
          </div>
          
          {/* Master Tabs */}
          <div className="flex justify-center gap-3 mb-8 flex-wrap">
            {masters.map((master) => (
              <button
                key={master.id}
                onClick={() => setSelectedMaster(master)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-medium transition-all ${
                  selectedMaster?.id === master.id
                    ? 'bg-[#D4A5A5] text-white shadow-lg'
                    : 'bg-white border-2 border-rose-200/50 text-gray-700 hover:border-[#D4A5A5]'
                }`}
                data-testid={`home-master-tab-${master.id}`}
              >
                {master.photo_url ? (
                  <img 
                    src={master.photo_url} 
                    alt={master.name}
                    className="w-6 h-6 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-rose-100 flex items-center justify-center">
                    <User className="w-3 h-3 text-[#D4A5A5]" />
                  </div>
                )}
                <span>{master.name}</span>
              </button>
            ))}
          </div>

          {/* Category Tabs */}
          {Object.keys(categoryLabels).length > 0 && (
            <div className="flex justify-center gap-2 mb-10 flex-wrap">
              {Object.entries(categoryLabels).map(([key, label]) => {
                const hasServices = (groupedServices[key] || []).length > 0;
                return (
                  <button
                    key={key}
                    onClick={() => setActiveCategory(key)}
                    disabled={!hasServices}
                    className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                      activeCategory === key
                        ? 'bg-[#9E829C] text-white'
                        : hasServices
                          ? 'bg-rose-50 text-gray-700 hover:bg-rose-100'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                    data-testid={`home-category-tab-${key}`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          )}
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500">
                <p>{selectedMaster ? `У майстра ${selectedMaster.name} ще немає послуг` : 'Оберіть майстра'}</p>
              </div>
            ) : (groupedServices[activeCategory] || []).length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500">
                <p>Немає послуг у цій категорії</p>
              </div>
            ) : (
              (groupedServices[activeCategory] || []).map((service, index) => (
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
                        <span>{service.duration_minutes} хв</span>
                      </div>
                      <p className="text-2xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>{service.price} ₴</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="text-center mt-12">
            <Button 
              onClick={() => navigate('/booking')} 
              className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white px-8 py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
              data-testid="services-book-button"
            >
              Обрати послугу і записатися
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
                  alt="Інтер'єр студії" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            <div className="space-y-6 order-1 lg:order-2">
              <p className="text-xs uppercase tracking-widest text-[#9E829C] font-medium">Про нас</p>
              <h3 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                Майстер з душею
              </h3>
              <div className="space-y-4 text-gray-600 leading-relaxed">
                <p>
                  Ласкаво просимо до нашої затишної студії! Я — професійний майстер манікюру та педикюру з понад 3-річним досвідом роботи.
                </p>
                <p>
                  Використовую тільки якісні матеріали та сучасні техніки. Кожен клієнт для мене особливий, і я прагну створити атмосферу комфорту та турботи.
                </p>
                <p>
                  Ваші руки і нігті заслуговують найкращого догляду. Довіртеся професіоналу і насолоджуйтеся результатом!
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="py-24 px-6 bg-white">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h3 className="text-4xl lg:text-5xl font-bold tracking-tight mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
              {settings.why_us_title || 'Чому обирають нас?'}
            </h3>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-8 rounded-2xl hover:shadow-lg transition-shadow" style={{ backgroundColor: themeColors.accent }}>
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: themeColors.primary }}>
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h4 className="text-xl font-semibold mb-3">
                {settings.why_us_reason_1 || 'Досвідчені майстри'}
              </h4>
            </div>
            <div className="text-center p-8 rounded-2xl hover:shadow-lg transition-shadow" style={{ backgroundColor: themeColors.accent }}>
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: themeColors.primary }}>
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h4 className="text-xl font-semibold mb-3">
                {settings.why_us_reason_2 || 'Якісні матеріали'}
              </h4>
            </div>
            <div className="text-center p-8 rounded-2xl hover:shadow-lg transition-shadow" style={{ backgroundColor: themeColors.accent }}>
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: themeColors.primary }}>
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h4 className="text-xl font-semibold mb-3">
                {settings.why_us_reason_3 || 'Стерильність та безпека'}
              </h4>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 bg-gradient-to-b from-white border-t" style={{ backgroundColor: themeColors.accent, borderColor: themeColors.border }}>
        <div className="container mx-auto max-w-7xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
            {/* Про студію */}
            <div>
              <h3 className="text-2xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif', color: themeColors.primary }}>
                {settings.site_name || 'Nail Studio'}
              </h3>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {settings.about_text || 'Професійна студія манікюру та педикюру з командою досвідчених майстрів. Ми створюємо красу та піклуємося про здоров\'я ваших нігтів.'}
              </p>
            </div>

            {/* Контакти */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-gray-900">Контакти</h4>
              <div className="space-y-3">
                {settings.phone && (
                  <a href={`tel:${settings.phone}`} className="flex items-center gap-3 text-gray-600 transition-colors" style={{ '&:hover': { color: themeColors.primary } }}>
                    <Phone className="h-5 w-5" />
                    <span>{settings.phone}</span>
                  </a>
                )}
                {settings.email && (
                  <a href={`mailto:${settings.email}`} className="flex items-center gap-3 text-gray-600 transition-colors" style={{ '&:hover': { color: themeColors.primary } }}>
                    <Mail className="h-5 w-5" />
                    <span>{settings.email}</span>
                  </a>
                )}
                {settings.address && (
                  <div className="flex items-center gap-3 text-gray-600">
                    <MapPin className="h-5 w-5" />
                    <span>{settings.address}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Графік та соц мережі */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-gray-900">Графік роботи</h4>
              {settings.working_hours && (
                <p className="text-gray-600 mb-6 whitespace-pre-line">{settings.working_hours}</p>
              )}
              
              {(settings.instagram || settings.facebook) && (
                <div className="flex gap-4 mt-6">
                  {settings.instagram && (
                    <a 
                      href={settings.instagram.startsWith('http') ? settings.instagram : `https://instagram.com/${settings.instagram.replace('@', '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 flex items-center justify-center text-white hover:scale-110 transition-transform"
                    >
                      <Instagram className="h-5 w-5" />
                    </a>
                  )}
                  {settings.facebook && (
                    <a 
                      href={settings.facebook.startsWith('http') ? settings.facebook : `https://facebook.com/${settings.facebook}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-10 h-10 rounded-full bg-[#1877F2] flex items-center justify-center text-white hover:scale-110 transition-transform"
                    >
                      <Facebook className="h-5 w-5" />
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Copyright */}
          <div className="pt-8 border-t text-center" style={{ borderColor: themeColors.border }}>
            <p className="text-gray-500 text-sm">© 2025 {settings.site_name || 'Nail Studio'}. Всі права захищені</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default HomePage;
