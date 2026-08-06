import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Calendar, Clock, Phone, Mail, User, Edit, Trash2, StickyNote, Save } from 'lucide-react';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

function AdminBookings() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedDate, setSelectedDate] = useState('');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingBooking, setEditingBooking] = useState(null);
  const [editDuration, setEditDuration] = useState(60);
  const [dailyNote, setDailyNote] = useState('');
  const [noteSaving, setNoteSaving] = useState(false);
  const [noteLoaded, setNoteLoaded] = useState(false);

  useEffect(() => {
    fetchBookings();
  }, []);

  useEffect(() => {
    if (selectedDate) {
      fetchDailyNote(selectedDate);
    } else {
      setDailyNote('');
      setNoteLoaded(false);
    }
  }, [selectedDate]);

  const getMasterId = () => user?.id;

  const fetchDailyNote = async (date) => {
    try {
      const masterId = getMasterId();
      if (!masterId) return;
      const res = await api.get(`/masters/${masterId}/notes/${date}`);
      setDailyNote(res.data.text || '');
      setNoteLoaded(true);
    } catch {
      setDailyNote('');
      setNoteLoaded(true);
    }
  };

  const saveDailyNote = async () => {
    const masterId = getMasterId();
    if (!masterId || !selectedDate) return;
    setNoteSaving(true);
    try {
      await api.put(`/masters/${masterId}/notes/${selectedDate}`, { text: dailyNote });
      toast.success('Нотатку збережено');
    } catch {
      toast.error('Помилка збереження нотатки');
    } finally {
      setNoteSaving(false);
    }
  };

  const fetchBookings = async () => {
    try {
      const response = await api.get('/admin/bookings');
      setBookings(response.data);
    } catch (error) {
      console.error('Booking fetch error:', error);
      toast.error('Помилка завантаження записів');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (bookingId, newStatus) => {
    try {
      await api.put(`/admin/bookings/${bookingId}`, { status: newStatus });
      toast.success('Статус оновлено');
      fetchBookings();
    } catch (error) {
      console.error('Status update error:', error);
      toast.error(error.response?.data?.detail || 'Помилка оновлення статусу');
    }
  };

  const handleOpenEditDialog = (booking) => {
    setEditingBooking(booking);
    setEditDuration(booking.duration_minutes);
    setEditDialogOpen(true);
  };

  const handleSaveBookingChanges = async () => {
    if (!editingBooking) return;
    
    try {
      await api.put(`/admin/bookings/${editingBooking.id}`, { 
        duration_minutes: editDuration,
        status: 'confirmed'
      });
      toast.success('Запис підтверджено з оновленою тривалістю');
      setEditDialogOpen(false);
      fetchBookings();
    } catch (error) {
      console.error('Booking update error:', error);
      toast.error(error.response?.data?.detail || 'Помилка оновлення запису');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'confirmed': return 'bg-green-100 text-green-800 border-green-200';
      case 'completed': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'cancelled': return 'bg-gray-100 text-gray-600 border-gray-200';
      default: return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'Очікує';
      case 'confirmed': return 'Підтверджено';
      case 'completed': return 'Завершено';
      case 'cancelled': return 'Скасовано';
      default: return status;
    }
  };

  const handleDeleteBooking = async (bookingId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цей запис? Цю дію неможливо скасувати.')) {
      return;
    }

    try {
      await api.delete(`/admin/bookings/${bookingId}`);
      toast.success('Запис успішно видалено');
      fetchBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка видалення запису');
    }
  };

  const filteredBookings = bookings.filter(booking => {
    // Фільтр по статусу
    const statusMatch = filterStatus === 'all' || booking.status === filterStatus;
    
    // Фільтр по даті
    const dateMatch = !selectedDate || booking.date === selectedDate;
    
    return statusMatch && dateMatch;
  });

  // Сортування за датою (найближчі спочатку)
  const sortedBookings = [...filteredBookings].sort((a, b) => {
    const dateA = new Date(a.date + ' ' + a.time);
    const dateB = new Date(b.date + ' ' + b.time);
    return dateA - dateB;
  });

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Записи
          </h1>
          <p className="text-gray-600 mt-2">Керування записами клієнтів</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="space-y-1">
            <Label htmlFor="date-filter" className="text-xs text-gray-500">Фільтр по даті</Label>
            <div className="flex gap-2">
              <Input
                id="date-filter"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-48"
                data-testid="filter-date"
              />
              {selectedDate && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedDate('')}
                  className="px-3"
                  data-testid="clear-date"
                >
                  ✕
                </Button>
              )}
            </div>
          </div>
          <div className="space-y-1">
            <Label htmlFor="status-filter" className="text-xs text-gray-500">Фільтр по статусу</Label>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger id="status-filter" className="w-48" data-testid="filter-status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Всі записи</SelectItem>
                <SelectItem value="pending">Очікують</SelectItem>
                <SelectItem value="confirmed">Підтверджені</SelectItem>
                <SelectItem value="completed">Завершені</SelectItem>
                <SelectItem value="cancelled">Скасовані</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Нотатки на день */}
      {selectedDate && noteLoaded && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5" data-testid="daily-notes-section">
          <div className="flex items-center gap-2 mb-3">
            <StickyNote className="h-5 w-5 text-amber-600" />
            <h3 className="font-semibold text-gray-800">Нотатки на {selectedDate}</h3>
          </div>
          <Textarea
            value={dailyNote}
            onChange={(e) => setDailyNote(e.target.value)}
            placeholder="Записати примітки на цей день..."
            className="bg-white border-amber-200 focus:border-amber-400 min-h-[80px] resize-y mb-3"
            data-testid="daily-note-input"
          />
          <Button
            onClick={saveDailyNote}
            disabled={noteSaving}
            size="sm"
            className="bg-amber-600 hover:bg-amber-700 text-white"
            data-testid="save-daily-note-btn"
          >
            <Save className="h-4 w-4 mr-1" />
            {noteSaving ? 'Збереження...' : 'Зберегти нотатку'}
          </Button>
        </div>
      )}

      {sortedBookings.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-rose-200/50">
          <p className="text-gray-500">
            {selectedDate 
              ? `Записів на ${selectedDate} не знайдено`
              : 'Записів не знайдено'}
          </p>
        </div>
      ) : (
        <div className="grid gap-6">
          {sortedBookings.map((booking) => (
            <div 
              key={booking.id} 
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-[0_2px_8px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all"
              data-testid={`booking-row-${booking.id}`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div className="flex-1 space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                        {booking.service_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(booking.status)}`}>
                          {getStatusText(booking.status)}
                        </span>
                      </div>
                    </div>
                    <p className="text-2xl font-bold text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {booking.price} ₴
                    </p>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Calendar className="h-4 w-4 text-[#D4A5A5]" />
                      <span>{booking.date}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="h-4 w-4 text-[#D4A5A5]" />
                      <span>{booking.time} ({booking.duration_minutes} хв)</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <User className="h-4 w-4 text-[#D4A5A5]" />
                      <span>{booking.client_name} {booking.client_surname || ''}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Phone className="h-4 w-4 text-[#D4A5A5]" />
                      <span>{booking.client_phone}</span>
                    </div>
                    {booking.client_email && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Mail className="h-4 w-4 text-[#D4A5A5]" />
                        <span>{booking.client_email}</span>
                      </div>
                    )}
                  </div>

                  {booking.notes && (
                    <div className="bg-[#F3EBEB] p-3 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Побажання</p>
                      <p className="text-sm">{booking.notes}</p>
                    </div>
                  )}
                </div>

                <div className="lg:w-64 space-y-2">
                  {booking.status === 'pending' && (
                    <Button
                      onClick={() => handleOpenEditDialog(booking)}
                      className="w-full bg-green-600 hover:bg-green-700 text-white"
                      data-testid={`confirm-with-duration-${booking.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Підтвердити з коригуванням
                    </Button>
                  )}
                  <div>
                    <label className="text-xs text-gray-500 mb-2 block">Змінити статус</label>
                    <Select 
                      value={booking.status} 
                      onValueChange={(value) => handleStatusChange(booking.id, value)}
                    >
                      <SelectTrigger data-testid={`status-select-${booking.id}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Очікує</SelectItem>
                        <SelectItem value="confirmed">Підтвердити</SelectItem>
                        <SelectItem value="completed">Завершити</SelectItem>
                        <SelectItem value="cancelled">Скасувати</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={() => handleDeleteBooking(booking.id)}
                    variant="outline"
                    className="w-full border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
                    data-testid={`delete-${booking.id}`}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Видалити запис
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Діалог редагування тривалості */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Підтвердження запису з коригуванням часу</DialogTitle>
            <DialogDescription>
              Скоригуйте тривалість послуги при необхідності
            </DialogDescription>
          </DialogHeader>
          
          {editingBooking && (
            <div className="space-y-4">
              <div className="bg-[#F3EBEB] p-4 rounded-lg space-y-2">
                <p className="text-sm font-medium">{editingBooking.service_name}</p>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>{editingBooking.date}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="h-4 w-4" />
                  <span>{editingBooking.time}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <User className="h-4 w-4" />
                  <span>{editingBooking.client_name} {editingBooking.client_surname || ''}</span>
                </div>
              </div>

              <div>
                <Label htmlFor="duration">Тривалість (хвилин)</Label>
                <Input
                  id="duration"
                  type="number"
                  min="15"
                  step="15"
                  value={editDuration}
                  onChange={(e) => setEditDuration(parseInt(e.target.value))}
                  className="mt-1"
                  data-testid="input-duration"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Оригінальна тривалість: {editingBooking.duration_minutes} хв
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setEditDialogOpen(false)}
            >
              Скасувати
            </Button>
            <Button 
              type="button"
              onClick={handleSaveBookingChanges}
              className="bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
              data-testid="save-duration-button"
            >
              Підтвердити запис
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminBookings;