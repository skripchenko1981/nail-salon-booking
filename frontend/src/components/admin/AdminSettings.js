import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Save, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminSettings() {
  const [settings, setSettings] = useState({
    site_name: '',
    site_description: '',
    primary_color: '#D4A5A5',
    secondary_color: '#9E829C',
    accent_color: '#F3EBEB',
    phone: '',
    email: '',
    address: '',
    instagram: '',
    facebook: '',
    working_hours: ''
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
        description: 'Оновіть сторінку щоб побачити зміни'
      });
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

        {/* Контактна інформація */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Контактна інформація
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="phone">Телефон</Label>
              <Input
                id="phone"
                value={settings.phone}
                onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                placeholder="+380 99 123 45 67"
                className="mt-1"
                data-testid="input-phone"
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={settings.email}
                onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                placeholder="info@beauty-alena.pp.ua"
                className="mt-1"
                data-testid="input-email"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="address">Адреса</Label>
              <Input
                id="address"
                value={settings.address}
                onChange={(e) => setSettings({ ...settings, address: e.target.value })}
                placeholder="Київ, вул. Прикладна, 1"
                className="mt-1"
                data-testid="input-address"
              />
            </div>
            <div>
              <Label htmlFor="working_hours">Години роботи</Label>
              <Input
                id="working_hours"
                value={settings.working_hours}
                onChange={(e) => setSettings({ ...settings, working_hours: e.target.value })}
                placeholder="Пн-Сб: 9:00-18:00"
                className="mt-1"
                data-testid="input-working-hours"
              />
            </div>
          </div>
        </div>

        {/* Соціальні мережі */}
        <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Соціальні мережі
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="instagram">Instagram</Label>
              <Input
                id="instagram"
                value={settings.instagram || ''}
                onChange={(e) => setSettings({ ...settings, instagram: e.target.value })}
                placeholder="https://instagram.com/your_account"
                className="mt-1"
                data-testid="input-instagram"
              />
            </div>
            <div>
              <Label htmlFor="facebook">Facebook</Label>
              <Input
                id="facebook"
                value={settings.facebook || ''}
                onChange={(e) => setSettings({ ...settings, facebook: e.target.value })}
                placeholder="https://facebook.com/your_page"
                className="mt-1"
                data-testid="input-facebook"
              />
            </div>
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
