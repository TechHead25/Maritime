import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Ship, Droplets, ArrowRight, Database, Lock, Activity } from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [videoDuration, setVideoDuration] = useState(0);

  // Scroll-based Video Scrubbing Effect
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!containerRef.current) return;
      
      const { top, height } = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      
      const scrollPosition = -top;
      const totalScrollable = height - windowHeight;
      
      let progress = 0;
      if (scrollPosition >= 0 && scrollPosition <= totalScrollable) {
        progress = scrollPosition / totalScrollable;
      } else if (scrollPosition > totalScrollable) {
        progress = 1;
      }
      
      setScrollProgress(progress);

      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (videoRef.current && videoDuration > 0) {
            // Smoothly scrub the video
            videoRef.current.currentTime = progress * videoDuration;
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, [videoDuration]);

  // Helper function to calculate smooth opacity for sections
  const getSectionStyles = (start: number, end: number, current: number) => {
    const fadeZone = 0.05; // 5% of scroll for fading in/out
    let opacity = 0;
    let translateY = 20; // start slightly lower

    if (current >= start && current <= end) {
      if (current < start + fadeZone) {
        // Fading in
        const ratio = (current - start) / fadeZone;
        opacity = ratio;
        translateY = 20 * (1 - ratio);
      } else if (current > end - fadeZone) {
        // Fading out
        const ratio = (end - current) / fadeZone;
        opacity = ratio;
        translateY = -20 * (1 - ratio);
      } else {
        // Fully visible
        opacity = 1;
        translateY = 0;
      }
    }

    return {
      opacity,
      transform: `translateY(${translateY}px)`,
      pointerEvents: opacity > 0.5 ? 'auto' : 'none' as const,
      position: 'absolute' as const,
      transition: 'opacity 0.1s linear, transform 0.1s linear',
      width: '100%',
      left: 0,
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
    };
  };

  return (
    <div style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-main)', minHeight: '100vh', overflow: 'hidden' }}>
      {/* Navbar (Glass) */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(4, 9, 20, 0.65)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Shield color="var(--accent-cyan)" size={24} />
          <span style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '0.05em' }}>
            MARITIME<span style={{ color: 'var(--accent-cyan)' }}>_OIL</span>
          </span>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <button style={navLinkStyle}>Capabilities</button>
          <button style={navLinkStyle}>Intelligence</button>
          <button style={navLinkStyle}>Security</button>
          <button
            onClick={() => navigate('/app')}
            style={{
              backgroundColor: 'var(--accent-blue)',
              color: '#fff',
              padding: '0.6rem 1.5rem',
              borderRadius: '8px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 15px rgba(14, 165, 233, 0.4)',
              transition: 'transform 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Enter Workspace <ArrowRight size={16} />
          </button>
        </div>
      </nav>

      {/* Main Scroll Scrubbing Container */}
      <div ref={containerRef} style={{ height: '400vh', position: 'relative' }}>
        
        {/* Sticky Video Background */}
        <div style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
          zIndex: 0,
        }}>
          {/* Overlay to ensure text readability */}
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to bottom, rgba(4, 9, 20, 0.8) 0%, rgba(4, 9, 20, 0.4) 50%, rgba(4, 9, 20, 0.95) 100%)',
            zIndex: 1,
          }} />
          
          <video
            ref={videoRef}
            src="https://images-assets.nasa.gov/video/GSFC_20161212_Ocean_m12456_Heat/GSFC_20161212_Ocean_m12456_Heat~large.mp4" 
            muted
            playsInline
            preload="auto"
            onLoadedMetadata={(e) => {
              const dur = e.currentTarget.duration;
              if (dur && isFinite(dur)) {
                setVideoDuration(dur);
              }
            }}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: 0.6,
            }}
          />
          
          {/* Dynamic Content based on scroll progress overlaid on the sticky video */}
          <div style={{
            position: 'absolute',
            inset: 0,
            zIndex: 2,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '0 2rem',
            textAlign: 'center',
          }}>
            
            {/* Slide 1: Hero (0-25%) */}
            <div style={getSectionStyles(0, 0.25, scrollProgress)}>
              <div style={{
                display: 'inline-block',
                padding: '0.4rem 1rem',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '20px',
                color: 'var(--accent-cyan)',
                fontWeight: 600,
                fontSize: '0.85rem',
                marginBottom: '1.5rem',
              }}>
                HISTORICAL MARITIME FORENSICS
              </div>
              <h1 style={{ fontSize: '4rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem', letterSpacing: '-0.02em', textShadow: '0 10px 30px rgba(0,0,0,0.8)' }}>
                Attribution Intelligence<br/>
                <span style={{ color: 'var(--accent-cyan)' }}>Without Compromise.</span>
              </h1>
              <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', maxWidth: '800px', margin: '0 auto 2.5rem', lineHeight: 1.6 }}>
                Advanced spatiotemporal analytics for historical maritime oil-spill forensic investigations.
                Uncover origin probability clouds using reverse Lagrangian drift simulations.
              </p>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                Scroll to explore <br/>
                <div style={{ width: '1px', height: '40px', background: 'linear-gradient(to bottom, rgba(255,255,255,0.4), transparent)' }} />
              </div>
            </div>

            {/* Slide 2: Pipeline (25-50%) */}
            <div style={getSectionStyles(0.25, 0.50, scrollProgress)}>
              <h2 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem', textShadow: '0 4px 10px rgba(0,0,0,0.5)' }}>The Scientific Engine</h2>
              <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '700px', margin: '0 auto 3rem' }}>
                Multi-factor data fusion bridging SAR backscatter observations with hydrodynamic particle modeling.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', maxWidth: '1000px', margin: '0 auto' }}>
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
                  <Droplets color="var(--accent-cyan)" size={32} style={{ marginBottom: '1rem' }} />
                  <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#fff' }}>1. Feature Extraction</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                    CFAR-based automated thresholding of Sentinel-1 imagery to isolate mineral oil anomalies from biogenic lookalikes.
                  </p>
                </div>
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
                  <Activity color="var(--accent-blue)" size={32} style={{ marginBottom: '1rem' }} />
                  <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#fff' }}>2. Backward Advection</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                    High-resolution Lagrangian particle tracking over ocean current and wind stress matrices.
                  </p>
                </div>
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
                  <Ship color="var(--accent-amber)" size={32} style={{ marginBottom: '1rem' }} />
                  <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#fff' }}>3. AIS Interception</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                    Candidate vessel track interpolation against origin probability envelopes to score attribution.
                  </p>
                </div>
              </div>
            </div>

            {/* Slide 3: Evidence & UI (50-75%) */}
            <div style={getSectionStyles(0.50, 0.75, scrollProgress)}>
              <h2 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '2rem' }}>Explainable Forensics</h2>
              <div className="glass-panel" style={{ padding: '2.5rem', maxWidth: '800px', margin: '0 auto', textAlign: 'left' }}>
                <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1.5rem', color: '#fff', marginBottom: '1rem' }}>Data Integrity First</h3>
                    <p style={{ color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '1rem' }}>
                      All calculations clearly distinguish between directly observed sensor data and model-derived simulations. 
                      Every evidence block includes quantitative uncertainty mapping.
                    </p>
                    <ul style={{ color: 'var(--text-dim)', fontSize: '0.9rem', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <li>✓ Non-accusatory evidence reporting</li>
                      <li>✓ Source metadata preservation</li>
                      <li>✓ Multi-factor liability scoring matrix</li>
                    </ul>
                  </div>
                  <div style={{ width: '250px', height: '250px', background: 'radial-gradient(circle, rgba(14,165,233,0.2) 0%, transparent 70%)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Database size={80} color="var(--accent-blue)" />
                  </div>
                </div>
              </div>
            </div>

            {/* Slide 4: CTA (75-100%) */}
            <div style={getSectionStyles(0.75, 1.0, scrollProgress)}>
              <h2 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>Ready for Investigation?</h2>
              <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem' }}>
                Access the forensic command center to explore case intelligence, verify attribution chains, and review the algorithmic models.
              </p>
              <button
                onClick={() => navigate('/app')}
                className="animate-pulseGlow"
                style={{
                  backgroundColor: 'var(--accent-blue)',
                  color: '#fff',
                  padding: '1rem 3rem',
                  borderRadius: '12px',
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '1rem',
                  boxShadow: '0 10px 25px rgba(14, 165, 233, 0.4)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  transition: 'transform 0.2s',
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Access Command Center <Lock size={20} />
              </button>
            </div>

          </div>
        </div>
      </div>

      {/* Static Footer Section (Appears after scrolling past the tall container) */}
      <footer style={{
        backgroundColor: '#030712',
        borderTop: '1px solid var(--border)',
        padding: '3rem 2rem',
        position: 'relative',
        zIndex: 10,
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '2rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <Shield color="var(--text-muted)" size={20} />
              <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-dim)' }}>
                SIH26143 / DECISION SUPPORT
              </span>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', maxWidth: '400px', lineHeight: 1.5 }}>
              This platform provides objective intelligence based on spatiotemporal and physical evidence models. It does not replace port state validation.
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '3rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <strong style={{ color: '#fff', fontSize: '0.9rem' }}>Technology</strong>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Sentinel-1 SAR</span>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Lagrangian Advection</span>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>AIS Telemetry Fusion</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <strong style={{ color: '#fff', fontSize: '0.9rem' }}>Protocol</strong>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Deterministic Processing</span>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>ISO 8601 UTC Time</span>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Zero Fabrication</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

const navLinkStyle: React.CSSProperties = {
  background: 'none',
  color: 'var(--text-muted)',
  fontSize: '0.95rem',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'color 0.2s',
};
