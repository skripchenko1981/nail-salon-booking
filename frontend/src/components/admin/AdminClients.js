import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { User, Phone, Mail, Calendar, TrendingUp, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminClients() {
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientBookings, setClientBookings] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      const [clientsRes, statsRes] = await Promise.all([
        axios.get(`${API}/admin/clients`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/clients/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setClients(clientsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast.error('Помилка завантаження клієнтів');
    } finally {
      setLoading(false);
    }
  };

  const handleViewClient = async (client) => {
    setSelectedClient(client);
    setDialogOpen(true);
    
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('master_token');
      const response = await axios.get(`${API}/admin/clients/${client.id}/bookings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClientBookings(response.data);
    } catch (error) {
      toast.error('Помилка завантаження історії');
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.phone.includes(searchTerm)
  );

  if (loading) {
    return <div className="text-center py-12">Завантаження...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
          База клієнтів
        </h1>
        <p className="text-gray-600 mt-2">Управління клієнтською базою та аналітика</p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-xl">
                <User className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Всього клієнтів</p>
                <p className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {stats.total_clients}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="bg-green-100 p-3 rounded-xl">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Нових цього місяця</p>
                <p className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {stats.new_clients_this_month}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="bg-purple-100 p-3 rounded-xl">
                <Calendar className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Постійні клієнти</p>
                <p className="text-3xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {stats.returning_clients}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Clients */}
      {stats && stats.top_clients.length > 0 && (
        <div className="bg-gradient-to-r from-[#F3EBEB] to-[#FDFCFB] rounded-2xl p-6 border border-rose-200/50">
          <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Топ-10 клієнтів за витратами
          </h3>
          <div className="grid gap-2">
            {stats.top_clients.slice(0, 5).map((client, index) => (
              <div key={index} className="flex justify-between items-center bg-white p-3 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="bg-[#D4A5A5] text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{client.name}</p>
                    <p className="text-xs text-gray-500">{client.phone}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-[#D4A5A5]">{client.total_spent} ₴</p>
                  <p className="text-xs text-gray-500">{client.completed_bookings} візитів</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-white rounded-2xl p-6 border border-rose-200/50">
        <Input
          placeholder="Пошук по імені або телефону..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
          data-testid="search-clients"
        />
      </div>

      {/* Clients List */}
      <div className="grid gap-4">
        {filteredClients.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-rose-200/50">
            <p className="text-gray-500">Клієнтів не знайдено</p>
          </div>
        ) : (
          filteredClients.map((client) => (
            <div 
              key={client.id} 
              className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-sm hover:shadow-md transition-all"
              data-testid={`client-card-${client.id}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="bg-[#F3EBEB] p-3 rounded-full">
                      <User className="h-5 w-5 text-[#D4A5A5]" />
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold">{client.name}</h4>
                      <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          {client.phone}
                        </span>
                        {client.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {client.email}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-rose-200/50">
                    <div>
                      <p className="text-xs text-gray-500">Всього візитів</p>
                      <p className="text-lg font-bold text-[#D4A5A5]">{client.total_bookings}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Завершено</p>
                      <p className="text-lg font-bold text-green-600">{client.completed_bookings}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Всього витрачено</p>
                      <p className="text-lg font-bold text-[#9E829C]">{client.total_spent} ₴</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Останній візит</p>
                      <p className="text-sm font-medium">{client.last_visit || 'Ще не було'}</p>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={() => handleViewClient(client)}
                  variant="outline"
                  size="sm"
                  className="ml-4"
                  data-testid={`view-client-${client.id}`}
                >
                  <Eye className="h-4 w-4 mr-1" />
                  Деталі
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Client Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Деталі клієнта</DialogTitle>
          </DialogHeader>
          
          {selectedClient && (
            <div className="space-y-6">
              {/* Client Info */}
              <div className="bg-[#F3EBEB] p-4 rounded-lg space-y-2">
                <h4 className="font-semibold text-lg">{selectedClient.name}</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-600">Телефон:</p>
                    <p className="font-medium">{selectedClient.phone}</p>
                  </div>
                  {selectedClient.email && (
                    <div>
                      <p className="text-gray-600">Email:</p>
                      <p className="font-medium">{selectedClient.email}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-gray-600">Перший візит:</p>
                    <p className="font-medium">{selectedClient.first_visit || 'Невідомо'}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Останній візит:</p>
                    <p className="font-medium">{selectedClient.last_visit || 'Ще не було'}</p>
                  </div>
                </div>
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{selectedClient.total_bookings}</p>
                  <p className="text-xs text-gray-600">Всього записів</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{selectedClient.completed_bookings}</p>
                  <p className="text-xs text-gray-600">Завершено</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">{selectedClient.total_spent} ₴</p>
                  <p className="text-xs text-gray-600">Витрачено</p>
                </div>
              </div>

              {/* Booking History */}
              <div>
                <h5 className="font-semibold mb-3">Історія візитів</h5>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {clientBookings.length === 0 ? (
                    <p className="text-gray-500 text-sm">Історії візитів немає</p>
                  ) : (
                    clientBookings.map((booking) => (
                      <div key={booking.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg text-sm">
                        <div>
                          <p className="font-medium">{booking.service_name}</p>
                          <p className="text-xs text-gray-500">{booking.date} о {booking.time}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{booking.price} ₴</p>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            booking.status === 'completed' ? 'bg-green-100 text-green-800' :
                            booking.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                            booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {booking.status === 'completed' ? 'Завершено' :
                             booking.status === 'confirmed' ? 'Підтверджено' :
                             booking.status === 'pending' ? 'Очікує' : 'Скасовано'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminClients;
