import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { ArrowLeft, Calendar, Clock, X } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { validateUkrainianPhone } from '../utils/phoneValidator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { Textarea } from '../components/ui/textarea';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function MyBookingsPage() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState('');
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [cancelBookingId, setCancelBookingId] = useState(null);
  const [cancellationReason, setCancellationReason] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!validateUkrainianPhone(phone)) {
      toast.error('Невірний формат телефону. Використовуйте формат: +380XXXXXXXXX');
      return;
    }
    
    setLoading(true);
    setSearched(true);
    
    try {
      const response = await axios.get(`${API}/bookings/client/${encodeURIComponent(phone)}`);
      setBookings(response.data);
      if (response.data.length === 0) {
        toast.info('Записів не знайдено', {
          description: 'Перевірте правильність номера телефону'
        });
      }
    } catch (error) {
      toast.error('Помилка при пошуку записів');
      setBookings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async () => {
    if (!cancelBookingId) return;
    
    try {
      await axios.put(`${API}/bookings/${cancelBookingId}/cancel`, {
        cancellation_reason: cancellationReason || undefined
      });
      toast.success('Запис скасовано');
      // Refresh bookings
      const response = await axios.get(`${API}/bookings/client/${encodeURIComponent(phone)}`);
      setBookings(response.data);
      setCancelBookingId(null);
      setCancellationReason('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Помилка при скасуванні запису');
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
      case 'pending': return 'Очікує підтвердження';
      case 'confirmed': return 'Підтверджено';
      case 'completed': return 'Завершено';
      case 'cancelled': return 'Скасовано';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB] py-12 px-6">
      <div className="noise-overlay"></div>
      
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <Button 
            onClick={() => navigate('/')} 
            variant="ghost" 
            className="mb-6 hover:bg-[#F3EBEB]"
            data-testid="back-to-home-button"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            На головну
          </Button>
          <h1 className="text-4xl lg:text-5xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
            Мої записи
          </h1>
          <p className="text-gray-600 mt-2">Знайдіть свої записи за номером телефону</p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-3xl p-8 lg:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-rose-200/50 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <Label htmlFor="phone">Номер телефону</Label>
              <Input
                id="phone"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+380 XX XXX XX XX"
                className="mt-1 border-rose-200/50 focus:ring-rose-300"
                data-testid="search-phone-input"
              />
              <p className="text-xs text-gray-500 mt-1">Формат: +380XXXXXXXXX</p>
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
              data-testid="search-bookings-button"
            >
              {loading ? 'Пошук...' : 'Знайти мої записи'}
            </Button>
          </form>
        </div>

        {/* Bookings List */}
        {searched && (
          <div className="space-y-4">
            {bookings.length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-rose-200/50">
                <p className="text-gray-500 text-lg">Записів не знайдено</p>
                <p className="text-gray-400 text-sm mt-2">Перевірте правильність номера телефону або створіть новий запис</p>
                <Button 
                  onClick={() => navigate('/booking')} 
                  className="mt-6 bg-[#D4A5A5] hover:bg-[#9E829C] text-white"
                  data-testid="create-booking-button"
                >
                  Створити запис
                </Button>
              </div>
            ) : (
              bookings.map((booking) => (
                <div 
                  key={booking.id} 
                  className="bg-white rounded-2xl p-6 lg:p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-rose-200/50"
                  data-testid={`booking-card-${booking.id}`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-2xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                        {booking.service_name}
                      </h3>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border mt-2 ${getStatusColor(booking.status)}`}>
                        {getStatusText(booking.status)}
                      </span>
                    </div>
                    {(booking.status === 'pending' || booking.status === 'confirmed') && (
                      <Button
                        onClick={() => setCancelBookingId(booking.id)}
                        variant="ghost"
                        size="icon"
                        className="hover:bg-red-50 hover:text-red-600"
                        data-testid={`cancel-booking-${booking.id}`}
                      >
                        <X className="h-5 w-5" />
                      </Button>
                    )}
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4 mt-6">
                    <div className="flex items-center gap-3">
                      <div className="bg-[#F3EBEB] p-3 rounded-xl">
                        <Calendar className="h-5 w-5 text-[#D4A5A5]" />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Дата</p>
                        <p className="font-medium">{booking.date}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="bg-[#F3EBEB] p-3 rounded-xl">
                        <Clock className="h-5 w-5 text-[#D4A5A5]" />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Час</p>
                        <p className="font-medium">{booking.time}</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-rose-200/50">
                    <div className="grid md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Клієнт</p>
                        <p className="font-medium">{booking.client_name} {booking.client_surname || ''}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Телефон</p>
                        <p className="font-medium">{booking.client_phone}</p>
                      </div>
                      {booking.client_email && (
                        <div>
                          <p className="text-gray-500">Email</p>
                          <p className="font-medium">{booking.client_email}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-gray-500">Вартість</p>
                        <p className="font-bold text-lg text-[#D4A5A5]" style={{ fontFamily: 'Playfair Display, serif' }}>
                          {booking.price} ₴
                        </p>
                      </div>
                    </div>
                    {booking.notes && (
                      <div className="mt-4">
                        <p className="text-gray-500 text-sm">Побажання</p>
                        <p className="text-sm mt-1">{booking.notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={!!cancelBookingId} onOpenChange={() => {
        setCancelBookingId(null);
        setCancellationReason('');
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Скасувати запис?</AlertDialogTitle>
            <AlertDialogDescription>
              Ви впевнені, що хочете скасувати цей запис? Ця дія незворотна.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="my-4">
            <Label htmlFor="cancellation_reason">Причина скасування (опціонально)</Label>
            <Textarea
              id="cancellation_reason"
              value={cancellationReason}
              onChange={(e) => setCancellationReason(e.target.value)}
              placeholder="Вкажіть причину скасування..."
              className="mt-2"
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-dialog-no">Ні, повернутися</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleCancelBooking}
              className="bg-red-600 hover:bg-red-700"
              data-testid="cancel-dialog-yes"
            >
              Так, скасувати
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default MyBookingsPage;