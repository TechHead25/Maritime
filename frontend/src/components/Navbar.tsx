import React from 'react';
import { HealthStatus } from '../types';

interface NavbarProps {
  health: HealthStatus | null;
  loadingHealth: boolean;
  errorHealth: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({ health, loadingHealth, errorHealth }) => {
  return (
    <header style={{
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border)',
      padding: '1rem 0'
    }}>
      <div className="container" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <img src="/orca-logo.png" alt="ORCA Logo" style={{ height: '32px', mixBlendMode: 'screen' }} />
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: '700', letterSpacing: '-0.02em' }}>
              ORCA Platform - Oil Spill Reconnaissance, Classification & Attribution
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Maritime Environmental Intelligence & Forensic Decision Support
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.4rem 0.8rem',
            borderRadius: '20px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            fontSize: '0.8rem'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: health?.status === 'healthy' ? '#10b981' : (errorHealth ? '#ef4444' : '#f59e0b'),
              display: 'inline-block'
            }} />
            <span>
              {loadingHealth ? 'Connecting API...' : (health ? `API Online (${health.version})` : 'API Disconnected')}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
