import React, { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({
    site_name: 'Nail Studio',
    site_description: 'Професійний догляд за вашими руками та ногами',
    primary_color: '#D4A5A5',
    secondary_color: '#9E829C',
    accent_color: '#F3EBEB',
    phone: '+380 99 123 45 67',
    email: 'info@beauty-alena.pp.ua',
    address: 'Київ, вул. Прикладна, 1',
    instagram: '',
    facebook: '',
    working_hours: 'Пн-Сб: 9:00-18:00'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
      applyColorsToDOM(response.data);
    } catch (error) {
      console.error('Помилка завантаження налаштувань:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyColorsToDOM = (settings) => {
    // Застосувати кольори через CSS змінні
    const root = document.documentElement;
    root.style.setProperty('--primary-color', settings.primary_color);
    root.style.setProperty('--secondary-color', settings.secondary_color);
    root.style.setProperty('--accent-color', settings.accent_color);
  };

  const refreshSettings = () => {
    fetchSettings();
  };

  return (
    <SettingsContext.Provider value={{ settings, loading, refreshSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};
