import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  apiGetMe,
  apiLogin,
  apiLogout,
  getAuthToken,
} from '../services/api';

export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at_utc: string;
  last_login_utc?: string | null;
  permissions: string[];
}

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (allowedRoles: UserRole[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      if (!token) {
        // Automatically attempt auto-login as default Analyst for streamlined developer experience
        try {
          const autoRes = await apiLogin({ username: 'analyst', password: 'Analyst@Forensic2026!' });
          setUser(autoRes.user);
        } catch {
          setUser(null);
        }
        return;
      }
      const profile = await apiGetMe();
      setUser(profile);
    } catch (e) {
      console.warn('Auth check failed:', e);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (username: string, password: string) => {
    const res = await apiLogin({ username, password });
    setUser(res.user);
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  const hasRole = (allowedRoles: UserRole[]): boolean => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions?.includes(permission) || false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user ? user.role : null,
        isAuthenticated: !!user,
        loading,
        login,
        logout,
        hasRole,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
