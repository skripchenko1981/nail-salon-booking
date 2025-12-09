import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Plus, Trash2, Eye, EyeOff, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminGallery() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    image_url: '',
    description: ''
  });

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      const response = await axios.get(`${API}/admin/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setImages(response.data);
    } catch (error) {
      toast.error('Помилка завантаження галереї');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    
    if (!formData.image_url) {
      toast.error('Додайте посилання на фото');
      return;
    }

    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      await axios.post(`${API}/admin/gallery`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Фото додано!');
      setDialogOpen(false);
      setFormData({ image_url: '', description: '' });
      fetchImages();
    } catch (error) {
      toast.error('Помилка додавання фото');
    }
  };

  const handleToggleActive = async (imageId, currentStatus) => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      await axios.put(`${API}/admin/gallery/${imageId}?is_active=${!currentStatus}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(currentStatus ? 'Фото приховано' : 'Фото показано');
      fetchImages();
    } catch (error) {
      toast.error('Помилка оновлення статусу');
    }
  };

  const handleDelete = async (imageId) => {
    if (!window.confirm('Видалити це фото?')) return;

    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      await axios.delete(`${API}/admin/gallery/${imageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Фото видалено');
      fetchImages();
    } catch (error) {
      toast.error('Помилка видалення фото');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Галерея робіт
          </h1>
          <p className="text-gray-600 mt-2">Додавайте фото ваших робіт для портфоліо</p>
        </div>
        <Button
          onClick={() => setDialogOpen(true)}
          className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
        >
          <Plus className="mr-2 h-4 w-4" />
          Додати фото
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-6 border border-rose-200/50">
          <p className="text-sm text-gray-600">Всього фото</p>
          <p className="text-3xl font-bold mt-1">{images.length}</p>
        </div>
        <div className="bg-white rounded-xl p-6 border border-rose-200/50">
          <p className="text-sm text-gray-600">Активні</p>
          <p className="text-3xl font-bold mt-1 text-green-600">
            {images.filter(img => img.is_active).length}
          </p>
        </div>
        <div className="bg-white rounded-xl p-6 border border-rose-200/50">
          <p className="text-sm text-gray-600">Приховані</p>
          <p className="text-3xl font-bold mt-1 text-gray-400">
            {images.filter(img => !img.is_active).length}
          </p>
        </div>
      </div>

      {/* Галерея */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {images.map((image) => (
          <div
            key={image.id}
            className={`relative group rounded-xl overflow-hidden border-2 ${
              image.is_active ? 'border-green-200' : 'border-gray-200 opacity-60'
            }`}
          >
            <img
              src={image.image_url}
              alt={image.description || 'Gallery image'}
              className="w-full h-64 object-cover"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/300x400?text=Фото+не+знайдено';
              }}
            />
            
            {/* Overlay з кнопками */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
              <Button
                size="sm"
                variant="outline"
                className="bg-white"
                onClick={() => handleToggleActive(image.id, image.is_active)}
              >
                {image.is_active ? (
                  <><EyeOff className="h-4 w-4 mr-1" /> Сховати</>
                ) : (
                  <><Eye className="h-4 w-4 mr-1" /> Показати</>
                )}
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleDelete(image.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            {/* Опис */}
            {image.description && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-3">
                <p className="text-white text-sm">{image.description}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {images.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl border border-rose-200/50">
          <ImageIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600">Ще немає фото в галереї</p>
          <p className="text-sm text-gray-400 mt-2">Додайте перше фото ваших робіт</p>
        </div>
      )}

      {/* Діалог додавання */}
      {dialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
              Додати фото
            </h3>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <Label htmlFor="image_url">Посилання на фото *</Label>
                <Input
                  id="image_url"
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  placeholder="https://example.com/image.jpg"
                  className="mt-1"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Завантажте фото на imgur.com або інший хостинг
                </p>
              </div>

              <div>
                <Label htmlFor="description">Опис (опціонально)</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Опишіть роботу..."
                  className="mt-1"
                  rows={3}
                />
              </div>

              {formData.image_url && (
                <div className="border rounded-lg p-2">
                  <p className="text-sm text-gray-600 mb-2">Попередній перегляд:</p>
                  <img
                    src={formData.image_url}
                    alt="Preview"
                    className="w-full h-48 object-cover rounded"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x200?text=Помилка+завантаження';
                    }}
                  />
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button type="submit" className="flex-1 bg-[#D4A5A5] hover:bg-[#9E829C] text-white">
                  Додати
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false);
                    setFormData({ image_url: '', description: '' });
                  }}
                  className="flex-1"
                >
                  Скасувати
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminGallery;
