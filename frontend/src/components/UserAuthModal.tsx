import React, { useState } from 'react';
import {
  Shield,
  User,
  LogOut,
  LogIn,
  CheckCircle2,
  AlertCircle,
  Lock,
} from 'lucide-react';
import { useAuth, UserRole } from '../context/AuthContext';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const UserAuthModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { user, login, logout } = useAuth();
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (u: string, p: string) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await login(u, p);
      setSuccess(`Authenticated successfully as ${u.toUpperCase()}`);
      setTimeout(() => {
        setSuccess(null);
        onClose();
      }, 800);
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please provide both username and password.');
      return;
    }
    handleLogin(username, password);
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await logout();
      setSuccess('Session revoked. Logged out.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const roleColors: Record<UserRole, string> = {
    ADMIN: '#f59e0b',
    ANALYST: '#38bdf8',
    VIEWER: '#10b981',
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 10, 20, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem',
    }}>
      <div style={{
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--glass-border)',
        borderRadius: '10px',
        width: '100%',
        maxWidth: '520px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.7)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: 'rgba(2, 132, 199, 0.15)',
              border: '1px solid var(--glass-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
            }}>
              <Shield size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                Enterprise Authentication & RBAC
              </h3>
              <div style={{ fontSize: '0.68rem', color: '#64748b' }}>
                Role-Based Access Control & Identity Verification
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.2rem' }}
          >
            ✕
          </button>
        </div>

        {/* Notices */}
        {error && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid var(--glass-border)',
            color: '#f87171',
            padding: '0.6rem 0.85rem',
            borderRadius: '6px',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}>
            <AlertCircle size={15} /> {error}
          </div>
        )}

        {success && (
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid var(--glass-border)',
            color: '#34d399',
            padding: '0.6rem 0.85rem',
            borderRadius: '6px',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}>
            <CheckCircle2 size={15} /> {success}
          </div>
        )}

        {/* Active Session Info */}
        {user ? (
          <div style={{
            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid var(--glass-border)',
            borderRadius: '8px',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: roleColors[user.role] || '#0284c7',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                }}>
                  {user.username.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: '0.90rem', fontWeight: 700, color: '#f8fafc' }}>
                    {user.full_name}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                    @{user.username} • {user.email}
                  </div>
                </div>
              </div>

              <span style={{
                fontSize: '0.70rem',
                fontWeight: 700,
                padding: '0.2rem 0.55rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(2, 132, 199, 0.15)',
                border: `1px solid ${roleColors[user.role]}`,
                color: roleColors[user.role],
              }}>
                {user.role}
              </span>
            </div>

            {/* Permissions List */}
            <div>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', display: 'block', marginBottom: '0.35rem' }}>
                GRANTED PERMISSIONS ({user.permissions?.length || 0})
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {user.permissions?.map((p) => (
                  <span
                    key={p}
                    style={{
                      fontSize: '0.62rem',
                      fontFamily: 'monospace',
                      backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                      color: '#cbd5e1',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '3px',
                      border: '1px solid var(--glass-border)',
                    }}
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={handleLogout}
              disabled={loading}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid var(--glass-border)',
                color: '#f87171',
                padding: '0.45rem',
                borderRadius: '5px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                marginTop: '0.5rem',
              }}
            >
              <LogOut size={14} /> Terminate Active Session (Logout)
            </button>
          </div>
        ) : (
          <div style={{
            backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid var(--glass-border)',
            borderRadius: '6px',
            padding: '0.85rem',
            fontSize: '0.75rem',
            color: '#94a3b8',
            textAlign: 'center',
          }}>
            No active session. Please authenticate below to access role-restricted operations.
          </div>
        )}

        {/* Quick Enterprise Role Switcher */}
        <div>
          <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748b', display: 'block', marginBottom: '0.4rem' }}>
            QUICK ROLE SWITCHER (PRE-CONFIGURED ENTERPRISE IDENTITIES)
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            <button
              onClick={() => handleLogin('admin', 'Admin@Enterprise2026!')}
              disabled={loading}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                color: '#fbbf24',
                padding: '0.55rem 0.4rem',
                borderRadius: '5px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.2rem',
              }}
            >
              <Shield size={14} />
              <span>ADMIN</span>
              <span style={{ fontSize: '0.58rem', color: '#94a3b8' }}>Full Access</span>
            </button>

            <button
              onClick={() => handleLogin('analyst', 'Analyst@Forensic2026!')}
              disabled={loading}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                color: '#38bdf8',
                padding: '0.55rem 0.4rem',
                borderRadius: '5px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.2rem',
              }}
            >
              <User size={14} />
              <span>ANALYST</span>
              <span style={{ fontSize: '0.58rem', color: '#94a3b8' }}>Investigations</span>
            </button>

            <button
              onClick={() => handleLogin('viewer', 'Viewer@Maritime2026!')}
              disabled={loading}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                color: '#34d399',
                padding: '0.55rem 0.4rem',
                borderRadius: '5px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.2rem',
              }}
            >
              <Lock size={14} />
              <span>VIEWER</span>
              <span style={{ fontSize: '0.58rem', color: '#94a3b8' }}>Read-Only</span>
            </button>
          </div>
        </div>

        {/* Custom Login Form */}
        <form onSubmit={handleCustomSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748b', display: 'block' }}>
            OR SIGN IN WITH CUSTOM CREDENTIALS
          </span>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                color: '#f8fafc',
                padding: '0.4rem 0.65rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                flex: 1,
                outline: 'none',
              }}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                color: '#f8fafc',
                padding: '0.4rem 0.65rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                flex: 1,
                outline: 'none',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              backgroundColor: '#0284c7',
              border: 'none',
              color: '#ffffff',
              padding: '0.45rem',
              borderRadius: '5px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.4rem',
            }}
          >
            <LogIn size={13} /> Sign In
          </button>
        </form>
      </div>
    </div>
  );
};
