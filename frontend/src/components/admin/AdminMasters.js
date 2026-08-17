import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Plus, Edit, Trash2, User, Mail, Phone } from 'lucide-react';
import api from '../../lib/api';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

function AdminMasters() {
  const [masters, setMasters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMaster, setEditingMaster] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    bio: '',
    photo_url: ''
  });

  useEffect(() => {
    fetchMasters();
  }, []);

  const fetchMasters = async () => {
    try {
      const response = await api.get('/masters');
      setMasters(response.data);
    } catch (error) {
      toast.error('Помилка завантаження майстрів');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (master = null) => {
    if (master) {
      setEditingMaster(master);
      setFormData({
        name: master.name,
        email: master.email,
        phone: master.phone,
        password: '',
        bio: master.bio || '',
        photo_url: master.photo_url || ''
      });
    } else {
      setEditingMaster(null);
      setFormData({
        name: '',
        email: '',
        phone: '',
        password: '',
        bio: '',
        photo_url: ''
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingMaster) {
        const updateData = { ...formData };
        delete updateData.password;
        
        await api.put(`/masters/${editingMaster.id}`, updateData);
        
        if (formData.password && formData.password.trim() !== '') {
          await api.put(`/masters/${editingMaster.id}/password`, { new_password: formData.password });
        }
        
        toast.success('Майстра оновлено');
      } else {
        await api.post('/masters', formData);
        toast.success('Майстра створено');
      }
      setDialogOpen(false);
      fetchMasters();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при збереженні');
    }
  };

  const handleDelete = async (masterId) => {
    const master = masters.find(m => m.id === masterId);
    const masterName = master?.name || 'цього майстра';
    
    if (!window.confirm(
      `УВАГА! Ви впевнені, що хочете видалити майстра "${masterName}"?\n\n` +
      `Це також видалить:\n` +
      `- Всі послуги майстра\n` +
      `- Весь графік роботи\n` +
      `- Всі бронювання\n` +
      `- Всі відпустки\n` +
      `- Всіх клієнтів\n` +
      `- Всі фото в галереї\n\n` +
      `Цю дію НЕ МОЖНА скасувати!`
    )) return;

    try {
      const response = await api.delete(`/masters/${masterId}`);
      
      const deleted = response.data.deleted;
      let details = [];
      if (deleted.services > 0) details.push(`${deleted.services} послуг`);
      if (deleted.schedule > 0) details.push(`${deleted.schedule} записів графіку`);
      if (deleted.bookings > 0) details.push(`${deleted.bookings} бронювань`);
      if (deleted.vacations > 0) details.push(`${deleted.vacations} відпусток`);
      if (deleted.clients > 0) details.push(`${deleted.clients} клієнтів`);
      if (deleted.gallery > 0) details.push(`${deleted.gallery} фото`);
      
      const detailsText = details.length > 0 ? ` та ${details.join(', ')}` : '';
      toast.success(`Майстра "${masterName}"${detailsText} видалено`, {
        duration: 5000
      });
      
      fetchMasters();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при видаленні');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Майстри
          </h1>
          <p className="text-gray-600 mt-2">Управління командою майстрів</p>
        </div>
        <Button
          onClick={() => handleOpenDialog()}
          className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
          data-testid="add-master-button"
        >
          <Plus className="mr-2 h-4 w-4" />
          Додати майстра
        </Button>
      </div>

      {masters.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-rose-200/50">
          <User className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Майстрів ще не додано</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {masters.map((master) => (
            <div
              key={master.id}
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all"
              data-testid={`master-${master.id}`}
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-16 h-16 rounded-full bg-[#F3EBEB] flex items-center justify-center">
                  {master.photo_url ? (
                    <img src={master.photo_url} alt={master.name} className="w-full h-full rounded-full object-cover" />
                  ) : (
                    <User className="h-8 w-8 text-[#D4A5A5]" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{master.name}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full ${master.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                    {master.is_active ? 'Активний' : 'Неактивний'}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Mail className="h-4 w-4 text-[#D4A5A5]" />
                  <span>{master.email}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="h-4 w-4 text-[#D4A5A5]" />
                  <span>{master.phone}</span>
                </div>
              </div>

              {master.bio && (
                <div className="mt-4 p-3 bg-[#F3EBEB] rounded-lg">
                  <p className="text-sm text-gray-700">{master.bio}</p>
                </div>
              )}

              <div className="flex gap-2 mt-4 pt-4 border-t border-rose-200/50">
                <Button
                  onClick={() => handleOpenDialog(master)}
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  data-testid={`edit-master-${master.id}`}
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Редагувати
                </Button>
                <Button
                  onClick={() => handleDelete(master.id)}
                  variant="outline"
                  size="sm"
                  className="text-red-600 hover:bg-red-50"
                  data-testid={`delete-master-${master.id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Діалог створення/редагування */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingMaster ? 'Редагувати майстра' : 'Додати майстра'}
            </DialogTitle>
            <DialogDescription>
              Заповніть інформацію про майстра
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Ім'я *</Label>
                <Input
                  id="name"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  data-testid="master-name-input"
                />
              </div>
              <div>
                <Label htmlFor="phone">Телефон *</Label>
                <Input
                  id="phone"
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+380501234567"
                  data-testid="master-phone-input"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                data-testid="master-email-input"
              />
            </div>

            <div>
              <Label htmlFor="password">
                Пароль {editingMaster && '(залиште порожнім, щоб не змінювати)'}
              </Label>
              <Input
                id="password"
                type="password"
                required={!editingMaster}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                data-testid="master-password-input"
              />
            </div>

            <div>
              <Label htmlFor="bio">Опис (необов'язково)</Label>
              <Textarea
                id="bio"
                value={formData.bio}
                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                placeholder="Інформація про майстра, досвід, спеціалізація..."
                data-testid="master-bio-input"
              />
            </div>

            <div>
              <Label htmlFor="photo_url">URL фото (необов'язково)</Label>
              <Input
                id="photo_url"
                value={formData.photo_url}
                onChange={(e) => setFormData({ ...formData, photo_url: e.target.value })}
                placeholder="https://..."
                data-testid="master-photo-input"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Скасувати
              </Button>
              <Button
                type="submit"
                className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                data-testid="master-save-button"
              >
                Зберегти
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminMasters;
