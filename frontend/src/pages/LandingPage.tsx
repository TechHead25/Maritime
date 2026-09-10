import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Ship, Droplets, ArrowRight, Database, Lock, Activity } from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [videoDuration, setVideoDuration] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);

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
  const getSectionStyles = (start: number, end: number, current: number): React.CSSProperties => {
    const fadeZone = 0.08;
    let opacity = 0;
    let translateY = 30;

    if (current >= start - fadeZone && current <= end + fadeZone) {
      if (current < start) {
        const ratio = 1 - (start - current) / fadeZone;
        opacity = ratio;
        translateY = 30 * (1 - ratio);
      } else if (current > end) {
        const ratio = 1 - (current - end) / fadeZone;
        opacity = ratio;
        translateY = -30 * (1 - ratio);
      } else {
        opacity = 1;
        translateY = 0;
      }
    }

    return {
      opacity,
      transform: `translateY(${translateY}px) scale(${opacity === 1 ? 1 : 0.98})`,
      pointerEvents: opacity > 0.5 ? 'auto' : 'none',
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      justifyContent: 'center',
      transition: 'opacity 0.1s ease-out, transform 0.1s ease-out',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    };
  };

  return (
    <div style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-main)', minHeight: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* Top Status Banner */}
      <div style={{
        background: 'linear-gradient(90deg, rgba(2,132,199,0.15) 0%, rgba(2,132,199,0.05) 100%)',
        borderBottom: '1px solid rgba(2,132,199,0.2)',
        padding: '0.4rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.75rem',
        color: 'var(--accent-cyan)',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span className="animate-pulse" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }}></span>
            SYSTEM NORMAL
          </span>
          <span style={{ opacity: 0.5 }}>|</span>
          <span>LAST TELEMETRY SYNC: {new Date().toISOString().substring(0, 19).replace('T', ' ')} UTC</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-dim)' }}>
          <span>v0.1.0-prod</span>
          <span>SIH26143</span>
        </div>
      </div>

      {/* Navbar (Glass) */}
      <nav style={{
        position: 'fixed',
        top: '32px',
        left: 0,
        right: 0,
        zIndex: 50,
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(4, 9, 20, 0.75)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ padding: '0.4rem', backgroundColor: 'var(--accent-blue)', borderRadius: '8px' }}>
            <Shield color="#fff" size={20} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '0.05em', lineHeight: 1 }}>
              ORCA
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', letterSpacing: '0.05em' }}>RECONNAISSANCE & CLASSIFICATION</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <div style={{ display: 'none', gap: '1.5rem' }}>
            {/* Keeping hidden on small screens for layout safety */}
          </div>
          <button style={navLinkStyle}>Platform</button>
          <button style={navLinkStyle}>Solutions</button>
          <button style={navLinkStyle}>Data Providers</button>
          <div style={{ width: '1px', height: '24px', backgroundColor: 'rgba(255,255,255,0.1)' }}></div>
          <button
            onClick={() => navigate('/app')}
            style={{
              backgroundColor: 'var(--accent-blue)',
              color: '#fff',
              padding: '0.6rem 1.5rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 20px rgba(2, 132, 199, 0.4)',
              transition: 'all 0.2s',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
            onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 25px rgba(2, 132, 199, 0.6)'; }}
            onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(2, 132, 199, 0.4)'; }}
          >
            Launch Console <ArrowRight size={16} />
          </button>
        </div>
      </nav>

      {/* Main Scroll Scrubbing Container */}
      <div ref={containerRef} style={{ height: '600vh', position: 'relative' }}>
        
        {/* Sticky Video Background */}
        <div style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
          zIndex: 0,
        }}>
          {/* Advanced Gradient Overlay */}
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(135deg, rgba(4, 9, 20, 0.9) 0%, rgba(4, 9, 20, 0.6) 40%, rgba(4, 9, 20, 0.95) 100%)',
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
              opacity: 0.8,
            }}
          />
          
          {/* Dynamic Content Container */}
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
            
            {/* Slide 1: Hero (0.0 to 0.15) */}
            <div style={getSectionStyles(0, 0.15, scrollProgress)}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1.25rem',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '30px',
                color: 'var(--accent-cyan)',
                fontWeight: 600,
                fontSize: '0.80rem',
                marginBottom: '2rem',
                backdropFilter: 'blur(10px)',
              }}>
                <Activity size={14} /> HIGH-PRECISION HISTORICAL FORENSICS
              </div>
              <h1 style={{ fontSize: '4.5rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem', letterSpacing: '-0.03em', textShadow: '0 10px 40px rgba(0,0,0,0.9)' }}>
                Attribution Intelligence<br/>
                <span style={{ color: 'var(--accent-cyan)', display: 'inline-block', marginTop: '0.5rem' }}>Without Compromise.</span>
              </h1>
              <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', maxWidth: '800px', margin: '0 auto 3rem', lineHeight: 1.6, textShadow: '0 2px 10px rgba(0,0,0,0.8)' }}>
                Advanced spatiotemporal analytics for historical maritime oil-spill forensic investigations.
                Uncover origin probability clouds using reverse Lagrangian drift simulations.
              </p>
              
              {/* Quick Stats Panel */}
              <div style={{
                display: 'flex',
                gap: '2rem',
                padding: '1.5rem 2.5rem',
                backgroundColor: 'rgba(12, 19, 34, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
              }}>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>10m</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>SAR Resolution</div>
                </div>
                <div style={{ width: '1px', backgroundColor: 'rgba(255,255,255,0.1)' }}></div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>99.9%</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Model Determinism</div>
                </div>
                <div style={{ width: '1px', backgroundColor: 'rgba(255,255,255,0.1)' }}></div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>Tier 1</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Data Integrity</div>
                </div>
              </div>

              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', marginTop: '3rem' }}>
                SCROLL TO EXPLORE THE PIPELINE <br/>
                <div style={{ width: '2px', height: '50px', background: 'linear-gradient(to bottom, rgba(56, 189, 248, 0.6), transparent)', borderRadius: '2px' }} />
              </div>
            </div>

            {/* Slide 2: Pipeline (0.20 to 0.35) */}
            <div style={getSectionStyles(0.20, 0.35, scrollProgress)}>
              <h2 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '1.5rem', textShadow: '0 4px 20px rgba(0,0,0,0.8)' }}>The Scientific Engine</h2>
              <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', maxWidth: '750px', margin: '0 auto 4rem', lineHeight: 1.6 }}>
                Multi-factor data fusion bridging SAR backscatter observations with rigorous hydrodynamic particle modeling and AIS telemetry.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', maxWidth: '1100px', margin: '0 auto' }}>
                <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'left', borderTop: '4px solid var(--accent-cyan)' }}>
                  <div style={{ padding: '1rem', backgroundColor: 'rgba(56, 189, 248, 0.1)', borderRadius: '12px', display: 'inline-block', marginBottom: '1.5rem' }}>
                    <Droplets color="var(--accent-cyan)" size={32} />
                  </div>
                  <h3 style={{ fontSize: '1.3rem', marginBottom: '1rem', color: '#fff', fontWeight: 700 }}>1. Feature Extraction</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                    CFAR-based automated thresholding of Sentinel-1 imagery to meticulously isolate mineral oil anomalies from biogenic lookalikes.
                  </p>
                </div>
                <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'left', borderTop: '4px solid var(--accent-blue)' }}>
                  <div style={{ padding: '1rem', backgroundColor: 'rgba(2, 132, 199, 0.1)', borderRadius: '12px', display: 'inline-block', marginBottom: '1.5rem' }}>
                    <Activity color="var(--accent-blue)" size={32} />
                  </div>
                  <h3 style={{ fontSize: '1.3rem', marginBottom: '1rem', color: '#fff', fontWeight: 700 }}>2. Backward Advection</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                    High-resolution Lagrangian particle tracking over verified ocean current grids and ECMWF ERA5 wind stress matrices.
                  </p>
                </div>
                <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'left', borderTop: '4px solid var(--accent-amber)' }}>
                  <div style={{ padding: '1rem', backgroundColor: 'rgba(245, 158, 11, 0.1)', borderRadius: '12px', display: 'inline-block', marginBottom: '1.5rem' }}>
                    <Ship color="var(--accent-amber)" size={32} />
                  </div>
                  <h3 style={{ fontSize: '1.3rem', marginBottom: '1rem', color: '#fff', fontWeight: 700 }}>3. AIS Interception</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                    Candidate vessel track interpolation against origin probability envelopes to output a non-accusatory attribution score.
                  </p>
                </div>
              </div>
            </div>

            {/* Slide 3: Global Satellite Coverage (0.40 to 0.55) */}
            <div style={getSectionStyles(0.40, 0.55, scrollProgress)}>
              <h2 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '2.5rem' }}>Global Integrations</h2>
              <div className="glass-panel" style={{ padding: '3.5rem', maxWidth: '1000px', margin: '0 auto', textAlign: 'left', display: 'flex', gap: '4rem', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1.8rem', color: '#fff', marginBottom: '1.5rem', fontWeight: 700 }}>Multi-Constellation Support</h3>
                  <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '1.1rem', marginBottom: '2rem' }}>
                    Seamlessly ingest historical Synthetic Aperture Radar (SAR) imagery from Copernicus Sentinel-1 and other orbital platforms. The system supports full-resolution GRD products and immutable NetCDF grids.
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    <div style={{ padding: '1.5rem', backgroundColor: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                      <strong style={{ color: 'var(--accent-cyan)', display: 'block', fontSize: '1.1rem', marginBottom: '0.3rem' }}>Copernicus CDSE</strong>
                      <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>Direct ESA archive queries for immediate SAR fetching.</span>
                    </div>
                    <div style={{ padding: '1.5rem', backgroundColor: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                      <strong style={{ color: 'var(--accent-blue)', display: 'block', fontSize: '1.1rem', marginBottom: '0.3rem' }}>ECMWF & CMEMS</strong>
                      <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>Hydrodynamic and atmospheric matrix fusion.</span>
                    </div>
                  </div>
                </div>
                <div style={{ width: '280px', height: '280px', background: 'radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 60%)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Database size={100} color="var(--accent-cyan)" />
                </div>
              </div>
            </div>

            {/* Slide 4: Evidence & UI (0.60 to 0.75) */}
            <div style={getSectionStyles(0.60, 0.75, scrollProgress)}>
              <h2 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '2.5rem' }}>Explainable Forensics</h2>
              <div className="glass-panel" style={{ padding: '3.5rem', maxWidth: '1000px', margin: '0 auto', textAlign: 'left', display: 'flex', gap: '4rem', alignItems: 'center', flexDirection: 'row-reverse' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1.8rem', color: '#fff', marginBottom: '1.5rem', fontWeight: 700 }}>Data Integrity First</h3>
                  <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '1.1rem', marginBottom: '1.5rem' }}>
                    All calculations clearly distinguish between directly observed sensor data and model-derived simulations. Every evidence block includes quantitative uncertainty mapping to ensure legal robustness.
                  </p>
                  <ul style={{ color: 'var(--text-main)', fontSize: '1rem', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}><span style={{ color: '#10b981' }}>✔</span> Non-accusatory evidence reporting</li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}><span style={{ color: '#10b981' }}>✔</span> Source metadata preservation lineage</li>
                    <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}><span style={{ color: '#10b981' }}>✔</span> Multi-factor liability scoring matrix</li>
                  </ul>
                </div>
                <div style={{ width: '280px', height: '280px', background: 'radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 60%)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Shield size={100} color="#10b981" />
                </div>
              </div>
            </div>

            {/* Slide 5: CTA (0.80 to 1.0) */}
            <div style={getSectionStyles(0.80, 1.0, scrollProgress)}>
              <div className="glass-panel" style={{ padding: '4rem', maxWidth: '800px', margin: '0 auto', border: '1px solid rgba(2, 132, 199, 0.3)', background: 'rgba(4, 9, 20, 0.85)' }}>
                <h2 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '1.5rem', color: '#fff' }}>Ready for Investigation?</h2>
                <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem', lineHeight: 1.6 }}>
                  Access the forensic command center to explore case intelligence, verify attribution chains, and deploy algorithmic models in a secure workspace.
                </p>
                <button
                  onClick={() => navigate('/app')}
                  className="animate-pulseGlow"
                  style={{
                    backgroundColor: 'var(--accent-blue)',
                    color: '#fff',
                    padding: '1.2rem 3.5rem',
                    borderRadius: '12px',
                    fontSize: '1.2rem',
                    fontWeight: 700,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '1rem',
                    boxShadow: '0 10px 30px rgba(2, 132, 199, 0.5)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    transition: 'all 0.2s',
                    cursor: 'pointer'
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 15px 40px rgba(2, 132, 199, 0.6)'; }}
                  onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 10px 30px rgba(2, 132, 199, 0.5)'; }}
                >
                  Access Command Center <Lock size={20} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Enterprise Footer Section */}
      <footer style={{
        backgroundColor: '#020610',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        padding: '5rem 2rem 2rem 2rem',
        position: 'relative',
        zIndex: 10,
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '3rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '3rem', marginBottom: '3rem' }}>
          
          {/* Brand Column */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
              <Shield color="var(--accent-blue)" size={24} />
              <span style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '0.05em', color: '#fff' }}>
                ORCA
              </span>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.95rem', maxWidth: '350px', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              Advanced spatiotemporal analytics platform for historical maritime oil-spill forensic investigations. Built for accuracy, transparency, and scientific integrity.
            </p>
            <div style={{ display: 'inline-flex', padding: '0.4rem 0.8rem', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '6px', color: '#10b981', fontSize: '0.75rem', fontWeight: 600 }}>
              SIH26143 MVP DEPLOYMENT
            </div>
          </div>
          
          {/* Tech Stack */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <strong style={{ color: '#fff', fontSize: '1.05rem', marginBottom: '0.5rem' }}>Technology</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Sentinel-1 SAR</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Lagrangian Advection</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>AIS Telemetry Fusion</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>FastAPI Engine</span>
          </div>

          {/* Protocols */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <strong style={{ color: '#fff', fontSize: '1.05rem', marginBottom: '0.5rem' }}>Protocols</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Deterministic Processing</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>ISO 8601 UTC Time</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Zero Fabrication Rule</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Data Integrity</span>
          </div>

          {/* Legal / Contact */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <strong style={{ color: '#fff', fontSize: '1.05rem', marginBottom: '0.5rem' }}>Organization</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Documentation</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Security Policy</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem', cursor: 'pointer' }}>Terms of Service</span>
          </div>
        </div>

        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
          <div>&copy; {new Date().getFullYear()} Maritime Oil-Spill Intelligence. All rights reserved.</div>
          <div>Decision Support System – Not an automated legal verdict tool.</div>
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
