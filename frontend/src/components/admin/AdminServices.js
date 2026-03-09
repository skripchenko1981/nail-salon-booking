import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Plus, Edit, Trash2, Clock, DollarSign } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CATEGORY_LABELS = {
  manicure: 'Манікюр',
  pedicure: 'Педікюр',
  podology: 'Подологія'
};

function AdminServices() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration_minutes: 60,
    price: 0,
    category: 'manicure',
    image_url: ''
  });

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const masterData = JSON.parse(localStorage.getItem('master_data') || '{"id": "admin"}');
      const masterId = masterData.id;
      const response = await axios.get(`${API}/services?master_id=${masterId}`);
      setServices(response.data);
    } catch (error) {
      toast.error('Помилка завантаження послуг');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (service = null) => {
    const masterData = JSON.parse(localStorage.getItem('master_data') || '{"id": "admin"}');
    const masterId = masterData.id;
    
    if (service) {
      setEditingService(service);
      setFormData({
        master_id: masterId,
        name: service.name,
        description: service.description,
        duration_minutes: service.duration_minutes,
        price: service.price,
        category: service.category || 'manicure',
        image_url: service.image_url || ''
      });
    } else {
      setEditingService(null);
      setFormData({
        master_id: masterId,
        name: '',
        description: '',
        duration_minutes: 60,
        price: 0,
        category: 'manicure',
        image_url: ''
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
    const masterData = JSON.parse(localStorage.getItem('master_data') || '{"id": "admin"}');
    const masterId = masterData.id;
    
    try {
      if (editingService) {
        await axios.put(
          `${API}/services/${editingService.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Послугу оновлено');
      } else {
        const serviceData = { ...formData, master_id: masterId };
        await axios.post(
          `${API}/services`,
          serviceData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Послугу створено');
      }
      setDialogOpen(false);
      fetchServices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при збереженні');
    }
  };

  const handleDelete = async (serviceId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цю послугу?')) return;
    
    const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
    try {
      await axios.delete(`${API}/services/${serviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Послугу видалено');
      fetchServices();
    } catch (error) {
      toast.error('Помилка при видаленні');
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
            Послуги
          </h1>
          <p className="text-gray-600 mt-2">Керування послугами та цінами</p>
        </div>
        <Button 
          onClick={() => handleOpenDialog()} 
          className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
          data-testid="add-service-button"
        >
          <Plus className="mr-2 h-4 w-4" />
          Додати послугу
        </Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {services.map((service) => (
          <div 
            key={service.id} 
            className="bg-white rounded-2xl overflow-hidden border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all"
            data-testid={`service-card-${service.id}`}
          >
            {service.image_url && (
              <div className="aspect-[4/3] overflow-hidden">
                <img 
                  src={service.image_url} 
                  alt={service.name} 
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="p-6 space-y-3">
              <h3 className="text-xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                {service.name}
              </h3>
              <p className="text-sm text-gray-600 line-clamp-2">{service.description}</p>
              <div className="flex items-center gap-4 text-sm text-gray-500 pt-2">
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {service.duration_minutes} хв
                </span>
                <span className="flex items-center gap-1 font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                  <DollarSign className="h-4 w-4" />
                  {service.price} ₴
                </span>
              </div>
              <div className="flex gap-2 pt-4 border-t border-rose-200/50">
                <Button 
                  onClick={() => handleOpenDialog(service)} 
                  variant="outline" 
                  size="sm" 
                  className="flex-1"
                  data-testid={`edit-service-${service.id}`}
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Редагувати
                </Button>
                <Button 
                  onClick={() => handleDelete(service.id)} 
                  variant="ghost" 
                  size="sm" 
                  className="text-red-600 hover:bg-red-50"
                  data-testid={`delete-service-${service.id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Service Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingService ? 'Редагувати послугу' : 'Додати послугу'}
            </DialogTitle>
            <DialogDescription>
              Заповніть інформацію про послугу
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Назва *</Label>
              <Input
                id="name"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                data-testid="service-name-input"
              />
            </div>
            <div>
              <Label htmlFor="description">Опис *</Label>
              <Textarea
                id="description"
                required
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                data-testid="service-description-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="duration">Тривалість (хв) *</Label>
                <Input
                  id="duration"
                  type="number"
                  required
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                  data-testid="service-duration-input"
                />
              </div>
              <div>
                <Label htmlFor="price">Ціна (₴) *</Label>
                <Input
                  id="price"
                  type="number"
                  required
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
                  data-testid="service-price-input"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="image_url">URL зображення</Label>
              <Input
                id="image_url"
                value={formData.image_url}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                placeholder="https://..."
                data-testid="service-image-input"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Скасувати
              </Button>
              <Button type="submit" className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white" data-testid="service-save-button">
                Зберегти
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminServices;