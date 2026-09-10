import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Compass,
  LayoutDashboard,
  FolderKanban,
  Radar,
  Ship,
  Database,
  FileText,
  Settings,
  Plus,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { fetchHealth } from '../../services/api';
import { HealthStatus } from '../../types';
import { NewInvestigationModal } from '../NewInvestigationModal';
import { UserAuthModal } from '../UserAuthModal';
import { useAuth } from '../../context/AuthContext';

export const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isNewCaseModalOpen, setIsNewCaseModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [utcTime, setUtcTime] = useState<string>('');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.warn('Health check failed:', err));

    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { label: 'Dashboard', to: '/app', icon: LayoutDashboard, exact: true },
    { label: 'Investigations', to: '/app/investigations', icon: FolderKanban, exact: false },
    { label: 'Live Maritime', to: '/app/live', icon: Radar, exact: false },
    { label: 'Vessel Intelligence', to: '/app/vessels', icon: Ship, exact: false },
    { label: 'Data Sources', to: '/app/data-sources', icon: Database, exact: false },
    { label: 'Reports', to: '/app/reports', icon: FileText, exact: false },
    { label: 'Settings', to: '/app/settings', icon: Settings, exact: false },
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: '#0a0f1d',
      color: '#f8fafc',
      overflow: 'hidden',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      {/* 1. Global Application Header */}
      <header style={{
        height: '56px',
        backgroundColor: 'var(--glass-panel)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.25rem',
        zIndex: 50,
        flexShrink: 0,
      }}>
        {/* Brand & Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            onClick={() => navigate('/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <img src="/orca-logo.png" alt="ORCA Logo" style={{ height: '28px', mixBlendMode: 'screen' }} />
              <div>
                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.01em' }}>
                  ORCA Platform - Oil Spill Reconnaissance, Classification & Attribution
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', letterSpacing: '0.04em' }}>
                  FORENSIC DECISION SUPPORT WORKSPACE
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Status, Data Freshness & User Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {/* System Status Pill */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            backgroundColor: health?.status === 'healthy' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
            border: `1px solid ${health?.status === 'healthy' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            padding: '0.25rem 0.65rem',
            borderRadius: '4px',
            fontSize: '0.72rem',
            fontWeight: 600,
            color: health?.status === 'healthy' ? '#34d399' : '#f87171',
          }}>
            <span style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: health?.status === 'healthy' ? '#10b981' : '#ef4444',
            }} />
            <span>{health?.status === 'healthy' ? 'OPERATIONAL' : 'OFFLINE'}</span>
          </div>

          {/* Data Freshness Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            backgroundColor: 'rgba(0,0,0,0.2)',
            border: '1px solid var(--glass-border)',
            padding: '0.25rem 0.65rem',
            borderRadius: '4px',
            fontFamily: 'monospace',
          }}>
            <Clock size={13} color="var(--accent-cyan)" />
            <span>{utcTime || 'UTC CLOCK'}</span>
          </div>

          {/* User Account / Role Widget */}
          <div
            onClick={() => setIsAuthModalOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              padding: '0.25rem 0.65rem',
              backgroundColor: 'rgba(0,0,0,0.2)',
              border: '1px solid var(--glass-border)',
              borderRadius: '4px',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            title="Manage Identity & RBAC Roles"
          >
            <div style={{
              width: '22px',
              height: '22px',
              borderRadius: '50%',
              backgroundColor: user?.role === 'ADMIN' ? 'var(--accent-amber)' : user?.role === 'VIEWER' ? '#10b981' : 'var(--accent-blue)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontSize: '0.65rem',
              fontWeight: 700,
            }}>
              {user ? user.username.slice(0, 2).toUpperCase() : 'FA'}
            </div>
            <div>
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>
                {user ? user.full_name : 'Forensic Analyst'}
              </span>
              <span style={{
                color: user?.role === 'ADMIN' ? '#fbbf24' : user?.role === 'VIEWER' ? '#34d399' : 'var(--accent-cyan)',
                fontSize: '0.65rem',
                fontWeight: 700,
                marginLeft: '0.35rem',
                padding: '0.05rem 0.3rem',
                borderRadius: '3px',
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
              }}>
                {user ? user.role : 'ANALYST'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Main Workspace Body (Sidebar + Content Viewport) */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <aside style={{
          width: isSidebarCollapsed ? '64px' : '230px',
          backgroundColor: 'var(--glass-panel)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          borderRight: '1px solid var(--glass-border)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          transition: 'width 0.2s ease',
          flexShrink: 0,
        }}>
          {/* Top Actions & Nav Links */}
          <div style={{ padding: '0.85rem 0.65rem' }}>
            {/* Quick Action: New Investigation Button */}
            <button
              onClick={() => setIsNewCaseModalOpen(true)}
              style={{
                width: '100%',
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                padding: isSidebarCollapsed ? '0.65rem 0' : '0.60rem 0.85rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.80rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
                gap: '0.5rem',
                marginBottom: '1.25rem',
                boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
              }}
              title="Create New Investigation"
            >
              <Plus size={16} />
              {!isSidebarCollapsed && <span>New Investigation</span>}
            </button>

            {/* Navigation List */}
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {navItems.map((item) => {
                const isActive = item.exact
                  ? location.pathname === item.to
                  : location.pathname.startsWith(item.to);

                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.exact}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: isSidebarCollapsed ? '0.65rem 0' : '0.60rem 0.85rem',
                      justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
                      borderRadius: '6px',
                      textDecoration: 'none',
                      fontSize: '0.82rem',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? '#38bdf8' : '#94a3b8',
                      backgroundColor: isActive ? 'rgba(2, 132, 199, 0.12)' : 'transparent',
                      borderLeft: isActive ? '3px solid #0284c7' : '3px solid transparent',
                      transition: 'all 0.15s ease',
                    }}
                    title={item.label}
                  >
                    <item.icon size={18} color={isActive ? '#38bdf8' : '#94a3b8'} />
                    {!isSidebarCollapsed && <span>{item.label}</span>}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer: Collapse Toggle & System Spec */}
          <div style={{
            padding: '0.75rem 0.65rem',
            borderTop: '1px solid #1e293b',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}>
            {!isSidebarCollapsed && (
              <div style={{ fontSize: '0.68rem', color: '#64748b', padding: '0 0.35rem' }}>
                <div>System Build: 0.1.0-prod</div>
                <div>Storage: Local Immutable</div>
              </div>
            )}
            <button
              onClick={() => setIsSidebarCollapsed((prev) => !prev)}
              style={{
                background: 'none',
                border: '1px solid #1e293b',
                color: '#94a3b8',
                padding: '0.4rem',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isSidebarCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <main style={{
          flex: 1,
          overflowY: 'auto',
          backgroundColor: '#0a0f1d',
          padding: '1.25rem',
        }}>
          <Outlet />
        </main>
      </div>

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isNewCaseModalOpen}
        onClose={() => setIsNewCaseModalOpen(false)}
        onCaseCreated={(createdCase) => {
          setIsNewCaseModalOpen(false);
          navigate(`/app/investigations/${createdCase.id}`);
        }}
      />

      {/* Enterprise User Authentication & RBAC Modal */}
      <UserAuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
};
