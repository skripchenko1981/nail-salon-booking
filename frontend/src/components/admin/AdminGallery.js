import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Plus, Trash2, Eye, EyeOff, Image as ImageIcon, Upload, X } from 'lucide-react';
import api from '../../lib/api';
import { toast } from 'sonner';

function AdminGallery() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [description, setDescription] = useState('');

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const response = await api.get('/admin/gallery');
      setImages(response.data);
    } catch {
      toast.error('Помилка завантаження галереї');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    const validFiles = [];
    const newPreviews = [];

    for (const file of files) {
      if (!file.type.startsWith('image/')) {
        toast.error(`${file.name}: не зображення`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`${file.name}: розмір > 10MB`);
        continue;
      }
      validFiles.push(file);
      newPreviews.push({ name: file.name, size: file.size, url: URL.createObjectURL(file) });
    }

    setSelectedFiles(prev => [...prev, ...validFiles]);
    setPreviews(prev => [...prev, ...newPreviews]);
  };

  const removeFile = (index) => {
    URL.revokeObjectURL(previews[index].url);
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!selectedFiles.length) {
      toast.error('Виберіть файли для завантаження');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      if (selectedFiles.length === 1) {
        const formData = new FormData();
        formData.append('file', selectedFiles[0]);
        if (description) formData.append('description', description);

        await api.post('/admin/gallery', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        toast.success('Фото завантажено!');
      } else {
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));
        if (description) formData.append('description', description);

        const res = await api.post('/admin/gallery/batch', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            setUploadProgress(Math.round((e.loaded * 100) / e.total));
          }
        });
        const { uploaded, errors } = res.data;
        toast.success(`Завантажено ${uploaded} фото`);
        if (errors.length > 0) {
          errors.forEach(err => toast.error(err));
        }
      }

      setDialogOpen(false);
      resetForm();
      fetchImages();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка завантаження');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const resetForm = () => {
    previews.forEach(p => URL.revokeObjectURL(p.url));
    setSelectedFiles([]);
    setPreviews([]);
    setDescription('');
  };

  const handleToggleActive = async (imageId, currentStatus) => {
    try {
      await api.put(`/admin/gallery/${imageId}?is_active=${!currentStatus}`, {});
      toast.success(currentStatus ? 'Фото приховано' : 'Фото показано');
      fetchImages();
    } catch {
      toast.error('Помилка оновлення статусу');
    }
  };

  const handleDelete = async (imageId) => {
    if (!window.confirm('Видалити це фото?')) return;
    try {
      await api.delete(`/admin/gallery/${imageId}`);
      toast.success('Фото видалено');
      fetchImages();
    } catch {
      toast.error('Помилка видалення фото');
    }
  };

  if (loading) return <div className="text-center py-12">Завантаження...</div>;

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
          data-testid="add-photo-btn"
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
          <p className="text-3xl font-bold mt-1 text-green-600">{images.filter(img => img.is_active).length}</p>
        </div>
        <div className="bg-white rounded-xl p-6 border border-rose-200/50">
          <p className="text-sm text-gray-600">Приховані</p>
          <p className="text-3xl font-bold mt-1 text-gray-400">{images.filter(img => !img.is_active).length}</p>
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
              src={image.thumb_url || image.image_url}
              alt={image.description || 'Gallery image'}
              className="w-full h-64 object-cover"
              loading="lazy"
              onError={(e) => { e.target.src = 'https://via.placeholder.com/300x400?text=Фото+не+знайдено'; }}
            />
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
              <Button size="sm" variant="outline" className="bg-white" onClick={() => handleToggleActive(image.id, image.is_active)}>
                {image.is_active ? <><EyeOff className="h-4 w-4 mr-1" /> Сховати</> : <><Eye className="h-4 w-4 mr-1" /> Показати</>}
              </Button>
              <Button size="sm" variant="destructive" onClick={() => handleDelete(image.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
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

      {/* Діалог завантаження */}
      {dialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
              Завантажити фото
            </h3>
            <form onSubmit={handleAdd} className="space-y-4">
              {/* Drop zone */}
              <div
                className="border-2 border-dashed border-rose-300 rounded-xl p-6 text-center hover:border-[#D4A5A5] transition-colors cursor-pointer"
                onClick={() => document.getElementById('gallery-file-input').click()}
                data-testid="gallery-drop-zone"
              >
                <Upload className="h-10 w-10 text-[#D4A5A5] mx-auto mb-3" />
                <p className="font-medium text-gray-700">Натисніть щоб вибрати фото</p>
                <p className="text-sm text-gray-500 mt-1">Можна вибрати декілька файлів (макс. 10MB кожен)</p>
                <input
                  id="gallery-file-input"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading}
                  data-testid="gallery-file-input"
                />
              </div>

              {/* Previews */}
              {previews.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700">Обрано файлів: {previews.length}</p>
                  <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                    {previews.map((preview, i) => (
                      <div key={i} className="relative group">
                        <img src={preview.url} alt={preview.name} className="w-full h-24 object-cover rounded-lg" />
                        <button
                          type="button"
                          onClick={() => removeFile(i)}
                          className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="h-3 w-3" />
                        </button>
                        <p className="text-xs text-gray-500 mt-0.5 truncate">{(preview.size / 1024 / 1024).toFixed(1)}MB</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Progress bar */}
              {uploading && uploadProgress > 0 && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-[#D4A5A5] h-2 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
                </div>
              )}

              <div>
                <Label htmlFor="description">Опис (опціонально)</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Опишіть роботу..."
                  className="mt-1"
                  rows={2}
                  disabled={uploading}
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  type="submit"
                  className="flex-1 bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                  disabled={uploading || !selectedFiles.length}
                  data-testid="upload-gallery-btn"
                >
                  {uploading ? `Завантаження... ${uploadProgress}%` : `Завантажити (${selectedFiles.length})`}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => { setDialogOpen(false); resetForm(); }}
                  className="flex-1"
                  disabled={uploading}
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
