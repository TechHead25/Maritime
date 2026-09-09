import React from 'react';
import {
  LayoutDashboard,
  Satellite,
  Droplets,
  Wind,
  Navigation,
  MapPin,
  Ship,
  BarChart3,
  FileText,
  Scale,
  Database,
  FileCheck,
} from 'lucide-react';

export type ConsoleNavSection =
  | 'overview'
  | 'sar'
  | 'slick'
  | 'environmental'
  | 'drift'
  | 'origin'
  | 'vessels'
  | 'attribution'
  | 'evidence'
  | 'uncertainty'
  | 'provenance'
  | 'reports';

interface Props {
  activeSection: ConsoleNavSection;
  onSelectSection: (section: ConsoleNavSection) => void;
  candidateCount?: number;
  slickDetected?: boolean;
}

interface NavItem {
  id: ConsoleNavSection;
  label: string;
  icon: React.ReactNode;
  badge?: string | number;
}

export const ConsoleNavPanel: React.FC<Props> = ({
  activeSection,
  onSelectSection,
  candidateCount = 0,
  slickDetected = false,
}) => {
  const items: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={15} /> },
    { id: 'sar', label: 'SAR Analysis', icon: <Satellite size={15} /> },
    {
      id: 'slick',
      label: 'Slick Detection',
      icon: <Droplets size={15} />,
      badge: slickDetected ? 'Detected' : undefined,
    },
    { id: 'environmental', label: 'Environmental Conditions', icon: <Wind size={15} /> },
    { id: 'drift', label: 'Drift Reconstruction', icon: <Navigation size={15} /> },
    { id: 'origin', label: 'Origin & Release Window', icon: <MapPin size={15} /> },
    {
      id: 'vessels',
      label: 'Vessel Correlation',
      icon: <Ship size={15} />,
      badge: candidateCount > 0 ? candidateCount : undefined,
    },
    { id: 'attribution', label: 'Attribution', icon: <BarChart3 size={15} /> },
    { id: 'evidence', label: 'Evidence Chain', icon: <FileText size={15} /> },
    { id: 'uncertainty', label: 'Uncertainty', icon: <Scale size={15} /> },
    { id: 'provenance', label: 'Data Provenance', icon: <Database size={15} /> },
    { id: 'reports', label: 'Reports & Dossier', icon: <FileCheck size={15} /> },
  ];

  return (
    <aside style={{
      width: '220px',
      backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      padding: '0.75rem 0.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.2rem',
      flexShrink: 0,
      boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
    }}>
      <div style={{
        padding: '0.4rem 0.6rem 0.6rem',
        borderBottom: '1px solid var(--glass-border)',
        marginBottom: '0.35rem',
      }}>
        <span style={{
          fontSize: '0.65rem',
          fontWeight: 700,
          color: '#64748b',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}>
          Forensic Workflow
        </span>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {items.map((item) => {
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectSection(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.45rem 0.65rem',
                borderRadius: '5px',
                border: 'none',
                backgroundColor: isActive ? 'rgba(2, 132, 199, 0.18)' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.76rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
                outline: 'none',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'rgba(30, 41, 59, 0.5)';
                  e.currentTarget.style.color = '#e2e8f0';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#94a3b8';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ color: isActive ? '#38bdf8' : '#64748b', display: 'flex' }}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>

              {item.badge !== undefined && (
                <span style={{
                  fontSize: '0.62rem',
                  padding: '0.1rem 0.35rem',
                  borderRadius: '3px',
                  backgroundColor: isActive ? '#0284c7' : '#1e293b',
                  color: '#ffffff',
                  fontWeight: 700,
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Scientific Transparency Pillar Notice */}
      <div style={{
        marginTop: 'auto',
        padding: '0.65rem',
        borderTop: '1px solid var(--glass-border)',
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        borderRadius: '6px',
        fontSize: '0.62rem',
        color: '#64748b',
        lineHeight: 1.4,
      }}>
        <div style={{ fontWeight: 700, color: '#94a3b8', marginBottom: '0.2rem' }}>
          SCIENTIFIC INTEGRITY
        </div>
        Deterministic reverse Lagrangian advection with strict empirical parameterization.
      </div>
    </aside>
  );
};
