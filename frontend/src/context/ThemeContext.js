import React, { createContext, useContext, useState, useEffect } from 'react';
import { themes } from '../themes';
import axios from 'axios';

const ThemeContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState('classic');
  const [themeColors, setThemeColors] = useState(themes.classic.colors);

  useEffect(() => {
    fetchTheme();
  }, []);

  const fetchTheme = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      const themeName = response.data.theme || 'classic';
      applyTheme(themeName);
    } catch (error) {
      console.error('Помилка завантаження теми:', error);
    }
  };

  const applyTheme = (themeName) => {
    const theme = themes[themeName] || themes.classic;
    setCurrentTheme(themeName);
    setThemeColors(theme.colors);
    
    // Застосувати кольори на body
    document.documentElement.style.setProperty('--primary-color', theme.colors.primary);
    document.documentElement.style.setProperty('--secondary-color', theme.colors.secondary);
    document.documentElement.style.setProperty('--accent-color', theme.colors.accent);
  };

  const refreshTheme = () => {
    fetchTheme();
  };

  return (
    <ThemeContext.Provider value={{ currentTheme, themeColors, refreshTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
