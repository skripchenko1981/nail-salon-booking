import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { ArrowLeft, Lock } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminLoginPage() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/admin/login`, credentials);
      localStorage.setItem('admin_token', response.data.token);
      localStorage.setItem('admin_username', response.data.username);
      toast.success('Ласкаво просимо!');
      navigate('/admin/analytics');
    } catch (error) {
      toast.error('Невірні облікові дані');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB] flex items-center justify-center py-12 px-6">
      <div className="noise-overlay"></div>
      
      <div className="w-full max-w-md relative z-10">
        <Button 
          onClick={() => navigate('/')} 
          variant="ghost" 
          className="mb-6 hover:bg-[#F3EBEB]"
          data-testid="back-to-home-button"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          На головну
        </Button>

        <div className="bg-white rounded-3xl p-8 lg:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-rose-200/50">
          <div className="text-center mb-8">
            <div className="bg-[#F3EBEB] w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lock className="h-8 w-8 text-[#D4A5A5]" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
              Вхід для адміністратора
            </h1>
            <p className="text-gray-600 mt-2 text-sm">Увійдіть для управління системою</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="username">Ім'я користувача</Label>
              <Input
                id="username"
                required
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                placeholder="admin"
                className="mt-1 border-rose-200/50 focus:ring-rose-300"
                data-testid="admin-username-input"
              />
            </div>
            <div>
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                required
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                placeholder="••••••••"
                className="mt-1 border-rose-200/50 focus:ring-rose-300"
                data-testid="admin-password-input"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-6 rounded-full text-base shadow-lg hover:shadow-xl active:scale-95 transition-all"
              data-testid="admin-login-button"
            >
              {loading ? 'Вхід...' : 'Увійти'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>За замовчуванням: admin / admin123</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminLoginPage;