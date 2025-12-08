import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Calendar, Plus, Edit, Trash2 } from 'lucide-react';
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

function AdminVacations() {
  const [vacations, setVacations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingVacation, setEditingVacation] = useState(null);
  const [formData, setFormData] = useState({
    master_id: '',
    start_date: '',
    end_date: '',
    reason: ''
  });

  useEffect(() => {
    fetchVacations();
  }, []);

  const fetchVacations = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${API}/vacations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVacations(response.data);
    } catch (error) {
      toast.error('Помилка завантаження відпусток');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (vacation = null) => {
    if (vacation) {
      setEditingVacation(vacation);
      setFormData({
        master_id: vacation.master_id,
        start_date: vacation.start_date,
        end_date: vacation.end_date,
        reason: vacation.reason || ''
      });
    } else {
      setEditingVacation(null);
      setFormData({
        master_id: '',
        start_date: '',
        end_date: '',
        reason: ''
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('admin_token');

    try {
      if (editingVacation) {
        await axios.put(
          `${API}/vacations/${editingVacation.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Відпустку оновлено');
      } else {
        await axios.post(
          `${API}/vacations`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success('Відпустку створено');
      }
      setDialogOpen(false);
      fetchVacations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при збереженні');
    }
  };

  const handleDelete = async (vacationId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цю відпустку?')) return;

    const token = localStorage.getItem('admin_token');
    try {
      await axios.delete(`${API}/vacations/${vacationId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Відпустку видалено');
      fetchVacations();
    } catch (error) {
      toast.error('Помилка при видаленні');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('uk-UA', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const getDuration = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
    return `${days} ${days === 1 ? 'день' : days < 5 ? 'дні' : 'днів'}`;
  };

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Відпустки та вихідні
          </h1>
          <p className="text-gray-600 mt-2">Планування відпусток майстрів</p>
        </div>
        <Button
          onClick={() => handleOpenDialog()}
          className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
          data-testid="add-vacation-button"
        >
          <Plus className="mr-2 h-4 w-4" />
          Додати відпустку
        </Button>
      </div>

      {vacations.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-rose-200/50">
          <Calendar className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Відпусток ще не заплановано</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {vacations.map((vacation) => (
            <div
              key={vacation.id}
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all"
              data-testid={`vacation-${vacation.id}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <Calendar className="h-5 w-5 text-[#D4A5A5]" />
                    <h3 className="font-semibold text-lg">
                      {formatDate(vacation.start_date)} — {formatDate(vacation.end_date)}
                    </h3>
                    <span className="text-sm text-gray-500">
                      ({getDuration(vacation.start_date, vacation.end_date)})
                    </span>
                  </div>
                  
                  {vacation.reason && (
                    <div className="bg-[#F3EBEB] p-3 rounded-lg mt-3">
                      <p className="text-sm text-gray-700">{vacation.reason}</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 ml-4">
                  <Button
                    onClick={() => handleOpenDialog(vacation)}
                    variant="outline"
                    size="sm"
                    data-testid={`edit-vacation-${vacation.id}`}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={() => handleDelete(vacation.id)}
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:bg-red-50"
                    data-testid={`delete-vacation-${vacation.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Діалог створення/редагування */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingVacation ? 'Редагувати відпустку' : 'Додати відпустку'}
            </DialogTitle>
            <DialogDescription>
              Вкажіть період відпустки або вихідних
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start_date">Дата початку *</Label>
                <Input
                  id="start_date"
                  type="date"
                  required
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  data-testid="vacation-start-date"
                />
              </div>
              <div>
                <Label htmlFor="end_date">Дата закінчення *</Label>
                <Input
                  id="end_date"
                  type="date"
                  required
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  data-testid="vacation-end-date"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="reason">Причина (необов'язково)</Label>
              <Textarea
                id="reason"
                value={formData.reason}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                placeholder="Наприклад: Відпустка, Лікарняний, Відрядження..."
                data-testid="vacation-reason"
              />
            </div>

            <div className="bg-[#F3EBEB] p-3 rounded-lg text-sm text-gray-600">
              💡 <strong>Підказка:</strong> У вибрані дати майстер не зможе приймати записи
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Скасувати
              </Button>
              <Button
                type="submit"
                className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                data-testid="vacation-save-button"
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

export default AdminVacations;
