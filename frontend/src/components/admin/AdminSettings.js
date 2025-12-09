import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Save, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSettings } from '../../context/SettingsContext';
import { useTheme } from '../../context/ThemeContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminSettings() {
  const { refreshSettings } = useSettings();
  const { refreshTheme } = useTheme();
  const [settings, setSettings] = useState({
    site_name: '',
    site_description: '',
    about_text: '',
    theme: 'classic',
    primary_color: '#D4A5A5',
    secondary_color: '#9E829C',
    accent_color: '#F3EBEB',
    phone: '',
    email: '',
    address: '',
    instagram: '',
    facebook: '',
    working_hours: '',
    // Контент головної сторінки
    hero_title: '',
    hero_subtitle: '',
    hero_button_text: '',
    services_title: '',
    services_subtitle: '',
    why_us_title: '',
    why_us_reason_1: '',
    why_us_reason_2: '',
    why_us_reason_3: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      toast.error('Помилка завантаження налаштувань');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const token = localStorage.getItem('admin_token');
      await axios.put(`${API}/admin/settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Налаштування збережено!', {
        description: 'Кольори застосовано автоматично'
      });
      // Оновити налаштування в контексті
      refreshSettings();
    } catch (error) {
      toast.error('Помилка збереження налаштувань');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
          Налаштування сайту
        </h1>
        <p className="text-gray-600 mt-2">Керування зовнішнім виглядом та контактною інформацією</p>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* Основна інформація */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Основна інформація
          </h3>
          <div className="grid gap-4">
            <div>
              <Label htmlFor="site_name">Назва сайту</Label>
              <Input
                id="site_name"
                value={settings.site_name}
                onChange={(e) => setSettings({ ...settings, site_name: e.target.value })}
                placeholder="Nail Studio"
                className="mt-1"
                data-testid="input-site-name"
              />
            </div>
            <div>
              <Label htmlFor="site_description">Опис сайту</Label>
              <Textarea
                id="site_description"
                value={settings.site_description}
                onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
                placeholder="Професійний догляд за вашими руками та ногами"
                className="mt-1"
                rows={3}
                data-testid="input-site-description"
              />
            </div>
            <div>
              <Label htmlFor="about_text">Про нас (у футері)</Label>
              <Textarea
                id="about_text"
                value={settings.about_text || ''}
                onChange={(e) => setSettings({ ...settings, about_text: e.target.value })}
                placeholder="Професійна студія манікюру та педикюру з командою досвідчених майстрів..."
                className="mt-1"
                rows={4}
                data-testid="input-about-text"
              />
            </div>
          </div>
        </div>

        {/* Контент головної сторінки */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Контент головної сторінки
          </h3>
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <p className="text-sm text-blue-800">
                💡 Тут ви можете змінити всі тексти на головній сторінці сайту
              </p>
            </div>
            
            {/* Hero секція */}
            <div className="border-l-4 border-[#D4A5A5] pl-4">
              <h4 className="font-semibold mb-3 text-gray-700">Головний банер (Hero)</h4>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="hero_title">Заголовок</Label>
                  <Input
                    id="hero_title"
                    value={settings.hero_title || ''}
                    onChange={(e) => setSettings({ ...settings, hero_title: e.target.value })}
                    placeholder="Ваша краса - наша пристрасть"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="hero_subtitle">Підзаголовок</Label>
                  <Input
                    id="hero_subtitle"
                    value={settings.hero_subtitle || ''}
                    onChange={(e) => setSettings({ ...settings, hero_subtitle: e.target.value })}
                    placeholder="Професійний манікюр та педикюр"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="hero_button_text">Текст кнопки</Label>
                  <Input
                    id="hero_button_text"
                    value={settings.hero_button_text || ''}
                    onChange={(e) => setSettings({ ...settings, hero_button_text: e.target.value })}
                    placeholder="Записатися онлайн"
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Секція послуг */}
            <div className="border-l-4 border-[#D4A5A5] pl-4">
              <h4 className="font-semibold mb-3 text-gray-700">Секція "Послуги"</h4>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="services_title">Заголовок</Label>
                  <Input
                    id="services_title"
                    value={settings.services_title || ''}
                    onChange={(e) => setSettings({ ...settings, services_title: e.target.value })}
                    placeholder="Наші послуги"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="services_subtitle">Підзаголовок</Label>
                  <Textarea
                    id="services_subtitle"
                    value={settings.services_subtitle || ''}
                    onChange={(e) => setSettings({ ...settings, services_subtitle: e.target.value })}
                    placeholder="Ми пропонуємо широкий спектр послуг..."
                    className="mt-1"
                    rows={2}
                  />
                </div>
              </div>
            </div>

            {/* Секція "Чому ми" */}
            <div className="border-l-4 border-[#D4A5A5] pl-4">
              <h4 className="font-semibold mb-3 text-gray-700">Секція "Чому обирають нас?"</h4>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="why_us_title">Заголовок</Label>
                  <Input
                    id="why_us_title"
                    value={settings.why_us_title || ''}
                    onChange={(e) => setSettings({ ...settings, why_us_title: e.target.value })}
                    placeholder="Чому обирають нас?"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="why_us_reason_1">Причина 1</Label>
                  <Input
                    id="why_us_reason_1"
                    value={settings.why_us_reason_1 || ''}
                    onChange={(e) => setSettings({ ...settings, why_us_reason_1: e.target.value })}
                    placeholder="Досвідчені майстри"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="why_us_reason_2">Причина 2</Label>
                  <Input
                    id="why_us_reason_2"
                    value={settings.why_us_reason_2 || ''}
                    onChange={(e) => setSettings({ ...settings, why_us_reason_2: e.target.value })}
                    placeholder="Якісні матеріали"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="why_us_reason_3">Причина 3</Label>
                  <Input
                    id="why_us_reason_3"
                    value={settings.why_us_reason_3 || ''}
                    onChange={(e) => setSettings({ ...settings, why_us_reason_3: e.target.value })}
                    placeholder="Стерильність та безпека"
                    className="mt-1"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Вибір теми */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Тематичне оформлення
          </h3>
          <div className="space-y-4">
            <div>
              <Label htmlFor="theme">Оберіть тему</Label>
              <select
                id="theme"
                value={settings.theme}
                onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#D4A5A5]"
              >
                <option value="classic">🎨 Класична (цілорічно)</option>
                <option value="winter">❄️ Новорічна (грудень-січень)</option>
                <option value="spring">🌸 Весняна (березень-травень)</option>
                <option value="summer">☀️ Літня (червень-серпень)</option>
                <option value="autumn">🍂 Осіння (вересень-листопад)</option>
              </select>
            </div>
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                💡 <strong>Підказка:</strong> Обрана тема автоматично змінить кольорову схему, фонові зображення та додасть тематичні декоративні елементи на всіх сторінках сайту.
              </p>
            </div>
          </div>
        </div>

        {/* Кольори */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Кольорова схема
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="primary_color">Основний колір</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="primary_color"
                  type="color"
                  value={settings.primary_color}
                  onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                  className="w-20 h-10 cursor-pointer"
                  data-testid="input-primary-color"
                />
                <Input
                  value={settings.primary_color}
                  onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                  placeholder="#D4A5A5"
                  className="flex-1"
                />
              </div>
              <div className="mt-2 p-4 rounded" style={{ backgroundColor: settings.primary_color }}>
                <p className="text-white text-center font-medium">Приклад</p>
              </div>
            </div>
            <div>
              <Label htmlFor="secondary_color">Додатковий колір</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="secondary_color"
                  type="color"
                  value={settings.secondary_color}
                  onChange={(e) => setSettings({ ...settings, secondary_color: e.target.value })}
                  className="w-20 h-10 cursor-pointer"
                  data-testid="input-secondary-color"
                />
                <Input
                  value={settings.secondary_color}
                  onChange={(e) => setSettings({ ...settings, secondary_color: e.target.value })}
                  placeholder="#9E829C"
                  className="flex-1"
                />
              </div>
              <div className="mt-2 p-4 rounded" style={{ backgroundColor: settings.secondary_color }}>
                <p className="text-white text-center font-medium">Приклад</p>
              </div>
            </div>
            <div>
              <Label htmlFor="accent_color">Акцентний колір</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="accent_color"
                  type="color"
                  value={settings.accent_color}
                  onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
                  className="w-20 h-10 cursor-pointer"
                  data-testid="input-accent-color"
                />
                <Input
                  value={settings.accent_color}
                  onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
                  placeholder="#F3EBEB"
                  className="flex-1"
                />
              </div>
              <div className="mt-2 p-4 rounded" style={{ backgroundColor: settings.accent_color }}>
                <p className="text-gray-700 text-center font-medium">Приклад</p>
              </div>
            </div>
          </div>
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 <strong>Порада:</strong> Кольори автоматично застосуються до кнопок, заголовків та акцентів на сайті
            </p>
          </div>
        </div>

        {/* Кнопки */}
        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={saving}
            className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
            data-testid="save-settings-button"
          >
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Збереження...' : 'Зберегти зміни'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => window.open('/', '_blank')}
          >
            <Eye className="mr-2 h-4 w-4" />
            Переглянути сайт
          </Button>
        </div>
      </form>
    </div>
  );
}

export default AdminSettings;
