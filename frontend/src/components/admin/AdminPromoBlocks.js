import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Plus, Edit, Trash2, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

function AdminPromoBlocks() {
  const [blocks, setBlocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingBlock, setEditingBlock] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    image_url: '',
    button_text: '',
    button_link: '',
    is_active: true,
    position: 0
  });

  useEffect(() => {
    fetchBlocks();
  }, []);

  const fetchBlocks = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${API}/api/admin/promo-blocks`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBlocks(response.data);
    } catch (error) {
      toast.error('Помилка завантаження блоків');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (block = null) => {
    if (block) {
      setEditingBlock(block);
      setFormData({
        title: block.title,
        description: block.description,
        image_url: block.image_url || '',
        button_text: block.button_text || '',
        button_link: block.button_link || '',
        is_active: block.is_active,
        position: block.position
      });
      setPreviewUrl(block.image_url || null);
      setSelectedFile(null);
    } else {
      setEditingBlock(null);
      setFormData({
        title: '',
        description: '',
        image_url: '',
        button_text: '',
        button_link: '',
        is_active: true,
        position: blocks.length
      });
      setPreviewUrl(null);
      setSelectedFile(null);
    }
    setDialogOpen(true);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Виберіть файл зображення');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('Розмір файлу не повинен перевищувати 10MB');
      return;
    }

    setSelectedFile(file);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('admin_token');
    setUploading(true);

    try {
      let imageUrl = formData.image_url;

      // Якщо вибрано новий файл - завантажити на S3
      if (selectedFile) {
        const uploadFormData = new FormData();
        uploadFormData.append('file', selectedFile);
        
        const uploadResponse = await axios.post(
          `${API}/api/admin/gallery`,
          uploadFormData,
          {
            headers: { 
              Authorization: `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        imageUrl = uploadResponse.data.image_url;
      }

      const blockData = {
        ...formData,
        image_url: imageUrl || undefined
      };

      if (editingBlock) {
        await axios.put(
          `${API}/api/admin/promo-blocks/${editingBlock.id}`,
          blockData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Блок оновлено');
      } else {
        await axios.post(
          `${API}/api/admin/promo-blocks`,
          blockData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Блок створено');
      }
      setDialogOpen(false);
      fetchBlocks();
    } catch (error) {
      console.error('Помилка:', error);
      toast.error(error.response?.data?.detail || 'Помилка збереження блоку');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (blockId) => {
    if (!window.confirm('Видалити цей блок?')) return;

    try {
      const token = localStorage.getItem('admin_token');
      await axios.delete(`${API}/api/admin/promo-blocks/${blockId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Блок видалено');
      fetchBlocks();
    } catch (error) {
      toast.error('Помилка видалення');
    }
  };

  const toggleActive = async (block) => {
    try {
      const token = localStorage.getItem('admin_token');
      await axios.put(
        `${API}/api/admin/promo-blocks/${block.id}`,
        { is_active: !block.is_active },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(block.is_active ? 'Блок приховано' : 'Блок показується');
      fetchBlocks();
    } catch (error) {
      toast.error('Помилка оновлення');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Промо-блоки
          </h1>
          <p className="text-gray-600 mt-2">Керування інформаційними блоками на головній сторінці</p>
        </div>
        <Button
          onClick={() => handleOpenDialog()}
          className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Додати блок
        </Button>
      </div>

      {blocks.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-rose-200/50">
          <p className="text-gray-500">Немає промо-блоків</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {blocks.map((block) => (
            <div
              key={block.id}
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)]"
            >
              <div className="flex gap-6">
                {block.image_url && (
                  <div className="w-48 h-32 rounded-lg overflow-hidden flex-shrink-0">
                    <img
                      src={block.image_url}
                      alt={block.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                
                <div className="flex-1">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold">{block.title}</h3>
                    <div className="flex gap-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        block.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {block.is_active ? 'Активний' : 'Прихований'}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                        Позиція: {block.position}
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-gray-600 mb-4">{block.description}</p>
                  
                  {(block.button_text || block.button_link) && (
                    <div className="text-sm text-gray-500 mb-4">
                      <span className="font-medium">Кнопка:</span> {block.button_text || 'Без тексту'}
                      {block.button_link && (
                        <span className="ml-2">→ {block.button_link}</span>
                      )}
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <Button
                      onClick={() => toggleActive(block)}
                      variant="outline"
                      size="sm"
                      className="border-blue-300"
                    >
                      {block.is_active ? (
                        <><EyeOff className="h-4 w-4 mr-2" />Приховати</>
                      ) : (
                        <><Eye className="h-4 w-4 mr-2" />Показати</>
                      )}
                    </Button>
                    <Button
                      onClick={() => handleOpenDialog(block)}
                      variant="outline"
                      size="sm"
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Редагувати
                    </Button>
                    <Button
                      onClick={() => handleDelete(block.id)}
                      variant="outline"
                      size="sm"
                      className="border-red-300 text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Видалити
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Діалог */}
      {dialogOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
              {editingBlock ? 'Редагувати блок' : 'Новий блок'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="title">Заголовок *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Наприклад: Спеціальна пропозиція!"
                  required
                  disabled={uploading}
                />
              </div>

              <div>
                <Label htmlFor="description">Опис *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Детальний опис промо-блоку..."
                  rows={4}
                  required
                  disabled={uploading}
                />
              </div>

              <div>
                <Label htmlFor="image">Зображення (опціонально)</Label>
                <Input
                  id="image"
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  disabled={uploading}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Підтримуються: JPG, PNG, WEBP, GIF (макс. 10MB)
                </p>
                
                {previewUrl && (
                  <div className="mt-3 border rounded-lg p-2">
                    <p className="text-sm text-gray-600 mb-2">Попередній перегляд:</p>
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="w-full h-48 object-cover rounded"
                    />
                  </div>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm font-medium text-blue-900 mb-2">💡 Кнопка на блоці (опціонально)</p>
                <p className="text-xs text-blue-700 mb-3">
                  Якщо заповните ці поля, на промо-блоці з'явиться кнопка.<br/>
                  <strong>Приклад:</strong> Текст: "Записатися", Посилання: "/booking"
                </p>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="button_text">Текст кнопки</Label>
                    <Input
                      id="button_text"
                      value={formData.button_text}
                      onChange={(e) => setFormData({ ...formData, button_text: e.target.value })}
                      placeholder="Детальніше"
                      disabled={uploading}
                    />
                  </div>
                  <div>
                    <Label htmlFor="button_link">Посилання</Label>
                    <Input
                      id="button_link"
                      value={formData.button_link}
                      onChange={(e) => setFormData({ ...formData, button_link: e.target.value })}
                      placeholder="/booking"
                      disabled={uploading}
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="position">Позиція</Label>
                  <Input
                    id="position"
                    type="number"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) })}
                    min="0"
                    disabled={uploading}
                  />
                  <p className="text-xs text-gray-500 mt-1">Чим менше число, тим вище показується</p>
                </div>
                <div className="flex items-center pt-6">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="mr-2"
                    disabled={uploading}
                  />
                  <Label htmlFor="is_active">Показувати на сайті</Label>
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button 
                  type="submit" 
                  className="flex-1 bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                  disabled={uploading}
                >
                  {uploading ? 'Завантаження...' : (editingBlock ? 'Зберегти' : 'Створити')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
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

export default AdminPromoBlocks;
