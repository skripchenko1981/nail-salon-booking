import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const AuthContext = createContext(null);

function loadInitialState() {
  const adminToken = localStorage.getItem('admin_token');
  const masterToken = localStorage.getItem('master_token');

  if (adminToken) {
    return {
      token: adminToken,
      role: 'admin',
      user: { username: localStorage.getItem('admin_username') || 'admin' },
    };
  }

  if (masterToken) {
    const masterData = JSON.parse(localStorage.getItem('master_data') || '{}');
    return {
      token: masterToken,
      role: 'master',
      user: masterData,
    };
  }

  return { token: null, role: null, user: null };
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(loadInitialState);

  const loginAdmin = useCallback((token, username) => {
    localStorage.setItem('admin_token', token);
    localStorage.setItem('admin_username', username);
    setAuth({ token, role: 'admin', user: { username } });
  }, []);

  const loginMaster = useCallback((token, masterData) => {
    localStorage.setItem('master_token', token);
    localStorage.setItem('master_data', JSON.stringify(masterData));
    setAuth({ token, role: 'master', user: masterData });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
    localStorage.removeItem('master_token');
    localStorage.removeItem('master_data');
    setAuth({ token: null, role: null, user: null });
  }, []);

  const value = useMemo(() => ({
    token: auth.token,
    role: auth.role,
    user: auth.user,
    isAdmin: auth.role === 'admin',
    isMaster: auth.role === 'master',
    isAuthenticated: !!auth.token,
    loginAdmin,
    loginMaster,
    logout,
  }), [auth, loginAdmin, loginMaster, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
