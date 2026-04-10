import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Send, Save, Info, ExternalLink, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Switch } from '../ui/switch';

const API = process.env.REACT_APP_BACKEND_URL;

export default function MasterTelegramSettings() {
  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState(null);

  const getHeaders = () => {
    const token = localStorage.getItem('master_token') || localStorage.getItem('token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  };

  const getMasterId = () => {
    const data = JSON.parse(localStorage.getItem('master_data') || '{}');
    return data.id;
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const masterId = getMasterId();
      if (!masterId) return;
      const res = await fetch(`${API}/api/masters/${masterId}`, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setBotToken(data.telegram_bot_token || '');
        setChatId(data.telegram_chat_id || '');
        setEnabled(data.telegram_notifications_enabled || false);
        setUnreadCount(data.unread_bookings_count || 0);
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const masterId = getMasterId();
      const res = await fetch(`${API}/api/masters/${masterId}/telegram`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({
          telegram_bot_token: botToken || null,
          telegram_chat_id: chatId || null,
          telegram_notifications_enabled: enabled,
        }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Налаштування збережено!' });
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Помилка збереження' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Помилка з\'єднання з сервером' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage(null);
    try {
      const masterId = getMasterId();
      const res = await fetch(`${API}/api/masters/${masterId}/test-telegram`, {
        method: 'POST',
        headers: getHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setMessage({ type: 'success', text: data.message });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Помилка тесту' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Помилка з\'єднання з сервером' });
    } finally {
      setTesting(false);
    }
  };

  const handleResetNotifications = async () => {
    try {
      const masterId = getMasterId();
      const res = await fetch(`${API}/api/masters/${masterId}/reset-notifications`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (res.ok) {
        setUnreadCount(0);
        setMessage({ type: 'success', text: 'Лічильник скинуто' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Помилка скидання' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16" data-testid="telegram-settings-loading">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#D4A5A5]" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl" data-testid="telegram-settings-page">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          Telegram сповіщення
        </h2>
        {unreadCount > 0 && (
          <button
            onClick={handleResetNotifications}
            className="flex items-center gap-2 px-3 py-1.5 bg-rose-100 text-rose-700 rounded-full text-sm font-medium hover:bg-rose-200 transition-colors"
            data-testid="reset-notifications-btn"
          >
            <Bell className="h-4 w-4" />
            {unreadCount} нових записів
          </button>
        )}
      </div>

      {/* Status message */}
      {message && (
        <div
          className={`flex items-center gap-2 p-3 rounded-lg mb-5 ${
            message.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
          }`}
          data-testid="telegram-status-message"
        >
          {message.type === 'success' ? <CheckCircle className="h-4 w-4 flex-shrink-0" /> : <AlertCircle className="h-4 w-4 flex-shrink-0" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6" data-testid="telegram-instructions">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-2">Як налаштувати Telegram бот:</p>
            <ol className="list-decimal pl-4 space-y-1.5">
              <li>
                Відкрийте{' '}
                <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="font-medium underline inline-flex items-center gap-1">
                  @BotFather <ExternalLink className="h-3 w-3" />
                </a>{' '}
                в Telegram
              </li>
              <li>Надішліть команду <code className="bg-blue-100 px-1 rounded">/newbot</code> та дайте ім'я боту</li>
              <li>Скопіюйте <strong>Bot Token</strong> та вставте нижче</li>
              <li>
                Відкрийте{' '}
                <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer" className="font-medium underline inline-flex items-center gap-1">
                  @userinfobot <ExternalLink className="h-3 w-3" />
                </a>{' '}
                щоб дізнатися ваш <strong>Chat ID</strong>
              </li>
              <li><strong>Важливо:</strong> Напишіть будь-яке повідомлення вашому новому боту перед тестом!</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Enable/Disable */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4" data-testid="telegram-enable-toggle">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {enabled ? <Bell className="h-5 w-5 text-[#D4A5A5]" /> : <BellOff className="h-5 w-5 text-gray-400" />}
            <div>
              <p className="font-medium text-gray-900">Сповіщення про нові записи</p>
              <p className="text-sm text-gray-500">Отримувати повідомлення в Telegram при новому записі</p>
            </div>
          </div>
          <Switch
            checked={enabled}
            onCheckedChange={setEnabled}
            data-testid="telegram-enabled-switch"
          />
        </div>
      </div>

      {/* Bot Token */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4" data-testid="telegram-bot-token-section">
        <label className="block text-sm font-medium text-gray-700 mb-2">Bot Token</label>
        <Input
          type="password"
          placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
          value={botToken}
          onChange={(e) => setBotToken(e.target.value)}
          className="font-mono text-sm"
          data-testid="telegram-bot-token-input"
        />
        <p className="text-xs text-gray-400 mt-1.5">Отримайте від @BotFather після створення бота</p>
      </div>

      {/* Chat ID */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6" data-testid="telegram-chat-id-section">
        <label className="block text-sm font-medium text-gray-700 mb-2">Chat ID</label>
        <Input
          type="text"
          placeholder="123456789"
          value={chatId}
          onChange={(e) => setChatId(e.target.value)}
          className="font-mono text-sm"
          data-testid="telegram-chat-id-input"
        />
        <p className="text-xs text-gray-400 mt-1.5">Дізнайтесь через @userinfobot (надішліть /start)</p>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-3" data-testid="telegram-action-buttons">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-[#D4A5A5] hover:bg-[#c49494] text-white"
          data-testid="telegram-save-btn"
        >
          <Save className="h-4 w-4 mr-2" />
          {saving ? 'Збереження...' : 'Зберегти'}
        </Button>
        <Button
          onClick={handleTest}
          disabled={testing || !botToken || !chatId}
          variant="outline"
          className="border-[#D4A5A5] text-[#D4A5A5] hover:bg-rose-50"
          data-testid="telegram-test-btn"
        >
          <Send className="h-4 w-4 mr-2" />
          {testing ? 'Відправка...' : 'Тест повідомлення'}
        </Button>
      </div>
    </div>
  );
}
