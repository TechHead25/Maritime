import React from 'react';
import { HealthStatus } from '../types';

interface Props {
  health?: HealthStatus | null;
  children: React.ReactNode;
  caseSelectorSlot?: React.ReactNode;
}

export const AppShell: React.FC<Props> = ({
  health,
  children,
  caseSelectorSlot,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      {/* Top Intelligence Header Bar */}
      <header style={{
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--glass-border)',
        padding: '0.75rem 1.5rem',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        backdropFilter: 'blur(10px)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {/* Brand / Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: 'var(--accent-blue)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: '1.1rem',
              fontWeight: 800,
            }}>
              ⚓
            </div>
            <div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
                ORCA Platform - Oil Spill Reconnaissance, Classification & Attribution
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 500 }}>
                Maritime Environmental Intelligence & Forensic Decision Support
              </div>
            </div>
          </div>

          {/* Center Case Selector Slot */}
          <div>
            {caseSelectorSlot}
          </div>

          {/* Right System Health Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.75rem',
              color: health ? '#10b981' : '#ef4444',
              backgroundColor: '#0f172a',
              border: '1px solid var(--glass-border)',
              padding: '0.3rem 0.6rem',
              borderRadius: '9999px',
            }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: health ? '#10b981' : '#ef4444',
                boxShadow: health ? '0 0 6px #10b981' : '0 0 6px #ef4444',
              }} />
              <span>{health ? `Backend Connected [v${health.version}]` : 'Backend Disconnected'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container-fluid" style={{ flex: 1, padding: '1.25rem 1.5rem' }}>
        {children}
      </main>

      {/* Footer */}
      <footer style={{
        backgroundColor: 'var(--bg-secondary)',
        borderTop: '1px solid var(--glass-border)',
        padding: '0.9rem 1.5rem',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        textAlign: 'center',
      }}>
        ORCA Platform - Oil Spill Reconnaissance, Classification & Attribution • Maritime Environmental Intelligence & Forensic Decision Support
      </footer>
    </div>
  );
};
