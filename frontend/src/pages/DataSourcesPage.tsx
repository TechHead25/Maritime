import React, { useState, useEffect } from 'react';
import {
  Satellite,
  Radio,
  Waves,
  Activity,
  Ship,
  Map as MapIcon,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Shield,
  Zap,
  Sliders,
  Compass,
} from 'lucide-react';
import {
  fetchControlCenterStatus,
  pingDataSource,
  configureDataSource,
} from '../services/api';

interface ProviderStatus {
  id: string;
  category: string;
  provider: string;
  service: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | 'UNCONFIGURED';
  authentication: {
    configured: boolean;
    auth_type: string;
    masked_credential: string;
    status: string;
  };
  last_successful_request_utc: string;
  last_data_timestamp_utc: string;
  latency_ms: number;
  coverage: string;
  rate_limit_status: string;
  errors: string | null;
  freshness: 'Fresh' | 'Aging' | 'Stale' | 'Unavailable';
  fallback_configured: boolean;
  fallback_provider: string | null;
}

export const DataSourcesPage: React.FC = () => {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeCategory, setActiveCategory] = useState<string>('ALL');
  const [pingingId, setPingingId] = useState<string | null>(null);
  const [pingResults, setPingResults] = useState<Record<string, { latency_ms: number; status: string }>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Configuration modal state
  const [configModalProvider, setConfigModalProvider] = useState<ProviderStatus | null>(null);
  const [configFallback, setConfigFallback] = useState<boolean>(true);
  const [configTimeout, setConfigTimeout] = useState<number>(10.0);
  const [configRateLimit, setConfigRateLimit] = useState<number>(60);
  const [isSavingConfig, setIsSavingConfig] = useState<boolean>(false);

  const loadControlCenter = async () => {
    try {
      setLoading(true);
      const data = await fetchControlCenterStatus();
      setProviders(data.providers || []);
    } catch (err) {
      console.warn('Failed to load control center telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadControlCenter();
  }, []);

  const handlePing = async (id: string) => {
    try {
      setPingingId(id);
      const res = await pingDataSource(id);
      setPingResults((prev) => ({
        ...prev,
        [id]: { latency_ms: res.latency_ms, status: res.status },
      }));
      setToastMessage(`Live ping succeeded for ${id}: ${res.latency_ms} ms (${res.status})`);
      setTimeout(() => setToastMessage(null), 5000);
      loadControlCenter();
    } catch (err: any) {
      alert(`Ping failed: ${err.message}`);
    } finally {
      setPingingId(null);
    }
  };

  const handleOpenConfig = (p: ProviderStatus) => {
    setConfigModalProvider(p);
    setConfigFallback(p.fallback_configured);
    setConfigTimeout(10.0);
    setConfigRateLimit(60);
  };

  const handleSaveConfig = async () => {
    if (!configModalProvider) return;
    try {
      setIsSavingConfig(true);
      await configureDataSource(configModalProvider.id, {
        fallback_enabled: configFallback,
        custom_timeout_seconds: configTimeout,
        rate_limit_rpm: configRateLimit,
      });
      setToastMessage(`Runtime configuration updated for ${configModalProvider.provider}`);
      setTimeout(() => setToastMessage(null), 5000);
      setConfigModalProvider(null);
      loadControlCenter();
    } catch (err: any) {
      alert(`Failed to save configuration: ${err.message}`);
    } finally {
      setIsSavingConfig(false);
    }
  };

  const categories = [
    'ALL',
    'Earth Observation',
    'AIS',
    'Ocean',
    'Weather',
    'Vessel Identity',
    'Basemap',
  ];

  const filteredProviders = providers.filter((p) => {
    if (activeCategory === 'ALL') return true;
    return p.category.toLowerCase() === activeCategory.toLowerCase();
  });

  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case 'earth observation':
        return <Satellite size={16} color="#38bdf8" />;
      case 'ais':
        return <Radio size={16} color="#10b981" />;
      case 'ocean':
        return <Waves size={16} color="#0284c7" />;
      case 'weather':
        return <Activity size={16} color="#fbbf24" />;
      case 'vessel identity':
        return <Ship size={16} color="#c084fc" />;
      case 'basemap':
        return <MapIcon size={16} color="#94a3b8" />;
      default:
        return <Compass size={16} color="#64748b" />;
    }
  };

  const getFreshnessBadge = (freshness: string) => {
    switch (freshness) {
      case 'Fresh':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', color: '#34d399', icon: <CheckCircle2 size={11} /> };
      case 'Aging':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', color: '#fbbf24', icon: <AlertTriangle size={11} /> };
      case 'Stale':
        return { bg: 'rgba(100, 116, 139, 0.15)', border: '#64748b', color: '#94a3b8', icon: <Clock size={11} /> };
      default:
        return { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', color: '#f87171', icon: <XCircle size={11} /> };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', color: '#34d399' };
      case 'DEGRADED':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', color: '#fbbf24' };
      case 'UNCONFIGURED':
        return { bg: 'rgba(100, 116, 139, 0.15)', border: '#64748b', color: '#94a3b8' };
      default:
        return { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', color: '#f87171' };
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.25rem',
      maxWidth: '1600px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 120px)',
    }}>
      {/* Toast Notice */}
      {toastMessage && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid var(--glass-border)',
          color: '#34d399',
          padding: '0.65rem 1rem',
          borderRadius: '6px',
          fontSize: '0.80rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <CheckCircle2 size={16} /> {toastMessage}
        </div>
      )}

      {/* Header Banner */}
      <div style={{
        backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--glass-border)',
        borderRadius: '8px',
        padding: '1.25rem 1.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
              Data Source Control Center
            </h1>
          </div>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '0.35rem 0 0', maxWidth: '720px' }}>
            Operational telemetry, authentication status, latency, and data freshness across all external satellite, meteorological, and maritime providers.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <button
            onClick={loadControlCenter}
            disabled={loading}
            style={{
              backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
              border: '1px solid var(--glass-border)',
              color: '#cbd5e1',
              padding: '0.45rem 0.95rem',
              borderRadius: '5px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <RefreshCw size={13} className={loading ? 'spin-icon' : ''} />
            Refresh Control Center
          </button>
        </div>
      </div>

      {/* Category Navigation Pills */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {categories.map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                backgroundColor: isActive ? '#0284c7' : '#0c1322',
                border: '1px solid',
                borderColor: isActive ? '#38bdf8' : '#1e293b',
                color: isActive ? '#ffffff' : '#94a3b8',
                padding: '0.4rem 0.85rem',
                borderRadius: '6px',
                fontSize: '0.76rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                transition: 'all 0.15s ease',
              }}
            >
              {cat !== 'ALL' && getCategoryIcon(cat)}
              <span>{cat}</span>
            </button>
          );
        })}
      </div>

      {/* Provider Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
        gap: '1.25rem',
      }}>
        {filteredProviders.map((p) => {
          const statusStyle = getStatusBadge(p.status);
          const freshStyle = getFreshnessBadge(p.freshness);
          const isPinging = pingingId === p.id;
          const pingResult = pingResults[p.id];

          return (
            <div
              key={p.id}
              style={{
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
                  <div style={{
                    marginTop: '0.15rem',
                    width: '32px',
                    height: '32px',
                    borderRadius: '6px',
                    backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {getCategoryIcon(p.category)}
                  </div>
                  <div>
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                      {p.category}
                    </span>
                    <h2 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f8fafc', margin: '0.1rem 0 0.2rem' }}>
                      {p.provider}
                    </h2>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                      {p.service}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem' }}>
                  {/* Status Badge */}
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    backgroundColor: statusStyle.bg,
                    border: `1px solid ${statusStyle.border}`,
                    color: statusStyle.color,
                  }}>
                    {p.status}
                  </span>

                  {/* Freshness Badge */}
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    padding: '0.1rem 0.45rem',
                    borderRadius: '3px',
                    backgroundColor: freshStyle.bg,
                    border: `1px solid ${freshStyle.border}`,
                    color: freshStyle.color,
                  }}>
                    {freshStyle.icon} {p.freshness.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '0.65rem',
                backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                border: '1px solid var(--glass-border)',
                borderRadius: '6px',
                padding: '0.85rem',
                fontSize: '0.75rem',
              }}>
                <div>
                  <span style={labelStyle}>AUTHENTICATION</span>
                  <div style={{ color: p.authentication.configured ? '#34d399' : '#fbbf24', fontWeight: 600 }}>
                    {p.authentication.status}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: '#64748b', fontFamily: 'monospace' }}>
                    {p.authentication.masked_credential}
                  </div>
                </div>

                <div>
                  <span style={labelStyle}>OBSERVED LATENCY</span>
                  <div style={{ color: '#38bdf8', fontWeight: 700, fontFamily: 'monospace' }}>
                    {pingResult ? `${pingResult.latency_ms} ms` : `${p.latency_ms} ms`}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: '#64748b' }}>
                    {pingResult ? `Live ping (${pingResult.status})` : 'Measured network latency'}
                  </div>
                </div>

                <div>
                  <span style={labelStyle}>LAST SUCCESSFUL REQUEST</span>
                  <div style={{ color: '#cbd5e1', fontSize: '0.70rem' }}>
                    {new Date(p.last_successful_request_utc).toISOString().replace('T', ' ').slice(0, 19)} UTC
                  </div>
                </div>

                <div>
                  <span style={labelStyle}>LATEST DATA TIMESTAMP</span>
                  <div style={{ color: '#cbd5e1', fontSize: '0.70rem' }}>
                    {new Date(p.last_data_timestamp_utc).toISOString().replace('T', ' ').slice(0, 19)} UTC
                  </div>
                </div>

                <div style={{ gridColumn: '1 / -1' }}>
                  <span style={labelStyle}>COVERAGE ENVELOPE</span>
                  <div style={{ color: '#94a3b8', fontSize: '0.70rem' }}>
                    {p.coverage}
                  </div>
                </div>

                <div style={{ gridColumn: '1 / -1' }}>
                  <span style={labelStyle}>RATE-LIMIT STATUS</span>
                  <div style={{ color: '#94a3b8', fontSize: '0.70rem' }}>
                    {p.rate_limit_status}
                  </div>
                </div>
              </div>

              {/* Error or Warning Banner if degraded */}
              {p.errors && (
                <div style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.10)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: '6px',
                  padding: '0.65rem 0.85rem',
                  fontSize: '0.72rem',
                  color: '#f87171',
                  lineHeight: 1.4,
                }}>
                  <strong>Operational Notice:</strong> {p.errors}
                </div>
              )}

              {/* Fallback configuration info */}
              {p.fallback_configured && p.fallback_provider && (
                <div style={{
                  backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: '6px',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.68rem',
                  color: '#64748b',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <span>Verified Fallback: <strong style={{ color: '#94a3b8' }}>{p.fallback_provider}</strong></span>
                  <span style={{ color: '#38bdf8' }}>Explicitly Authorized</span>
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto', paddingTop: '0.4rem' }}>
                <button
                  onClick={() => handlePing(p.id)}
                  disabled={isPinging}
                  style={{
                    backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)',
                    color: '#38bdf8',
                    padding: '0.42rem 0.85rem',
                    borderRadius: '5px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: isPinging ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    flex: 1,
                    justifyContent: 'center',
                  }}
                >
                  {isPinging ? <RefreshCw size={12} className="spin-icon" /> : <Zap size={12} />}
                  {isPinging ? 'Pinging...' : 'Test Connection'}
                </button>

                <button
                  onClick={() => handleOpenConfig(p)}
                  style={{
                    backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)',
                    color: '#cbd5e1',
                    padding: '0.42rem 0.85rem',
                    borderRadius: '5px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <Sliders size={12} /> Configure
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Configuration Modal */}
      {configModalProvider && (
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
            maxWidth: '560px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.7)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                  Provider Configuration
                </span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: '0.1rem 0' }}>
                  {configModalProvider.provider}
                </h3>
              </div>
              <button
                onClick={() => setConfigModalProvider(null)}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            {/* Security Guardrail Notice */}
            <div style={{
              backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
              border: '1px solid var(--glass-border)',
              borderRadius: '6px',
              padding: '0.85rem',
              fontSize: '0.72rem',
              color: '#94a3b8',
              lineHeight: 1.4,
            }}>
              <strong style={{ color: '#f8fafc' }}>Credential Security Policy:</strong> API tokens and client secrets are managed exclusively through environment configuration (<code style={{ color: '#38bdf8' }}>.env</code>). Secrets are never exposed to the frontend client.
            </div>

            {/* Config Fields */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', cursor: 'pointer', fontSize: '0.78rem', color: '#f8fafc' }}>
                <input
                  type="checkbox"
                  checked={configFallback}
                  onChange={(e) => setConfigFallback(e.target.checked)}
                />
                Allow verified historical archive fallback if external endpoint is unavailable
              </label>

              <div>
                <label style={labelStyle}>HTTP SOCKET TIMEOUT (SECONDS)</label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={configTimeout}
                  onChange={(e) => setConfigTimeout(Number(e.target.value))}
                  style={{
                    backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)',
                    color: '#f8fafc',
                    padding: '0.4rem 0.65rem',
                    borderRadius: '4px',
                    fontSize: '0.78rem',
                    width: '100%',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={labelStyle}>RATE LIMIT CAP (REQUESTS / MINUTE)</label>
                <input
                  type="number"
                  min="10"
                  max="600"
                  value={configRateLimit}
                  onChange={(e) => setConfigRateLimit(Number(e.target.value))}
                  style={{
                    backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)',
                    color: '#f8fafc',
                    padding: '0.4rem 0.65rem',
                    borderRadius: '4px',
                    fontSize: '0.78rem',
                    width: '100%',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.65rem', marginTop: '0.5rem' }}>
              <button
                onClick={() => setConfigModalProvider(null)}
                style={{
                  backgroundColor: 'var(--glass-panel)', backdropFilter: 'var(--glass-blur)', WebkitBackdropFilter: 'var(--glass-blur)',
                  border: '1px solid var(--glass-border)',
                  color: '#cbd5e1',
                  padding: '0.45rem 0.85rem',
                  borderRadius: '5px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>

              <button
                onClick={handleSaveConfig}
                disabled={isSavingConfig}
                style={{
                  backgroundColor: '#0284c7',
                  border: 'none',
                  color: '#ffffff',
                  padding: '0.45rem 1rem',
                  borderRadius: '5px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: isSavingConfig ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                {isSavingConfig ? <RefreshCw size={13} className="spin-icon" /> : <CheckCircle2 size={13} />}
                {isSavingConfig ? 'Saving...' : 'Apply Configuration'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: '#64748b',
  display: 'block',
  marginBottom: '0.2rem',
  letterSpacing: '0.03em',
};
