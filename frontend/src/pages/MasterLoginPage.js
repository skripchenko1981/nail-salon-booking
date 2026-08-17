import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { LogIn } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';

function MasterLoginPage() {
  const navigate = useNavigate();
  const { loginMaster } = useAuth();
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/masters/login', credentials);
      loginMaster(response.data.token, response.data.master);
      toast.success('Успішний вхід!');
      navigate('/master/dashboard');
    } catch (error) {
      toast.error('Невірний email або пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FDFCFB] via-[#F3EBEB] to-[#FDFCFB] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-3xl shadow-2xl p-8 border border-rose-200/50">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-block p-4 bg-[#F3EBEB] rounded-full mb-4">
              <LogIn className="h-8 w-8 text-[#D4A5A5]" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
              Вхід для майстра
            </h1>
            <p className="text-gray-600">Введіть свої дані для входу</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                placeholder="your.email@example.com"
                value={credentials.email}
                onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
                className="mt-1"
                data-testid="input-email"
              />
            </div>

            <div>
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                required
                placeholder="••••••••"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="mt-1"
                data-testid="input-password"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#D4A5A5] hover:bg-[#9E829C] text-white py-3 text-lg"
              data-testid="login-button"
            >
              {loading ? 'Вхід...' : 'Увійти'}
            </Button>
          </form>

          {/* Back to Home */}
          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-600 hover:text-[#D4A5A5] transition-colors"
            >
              ← Повернутися на головну
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MasterLoginPage;
