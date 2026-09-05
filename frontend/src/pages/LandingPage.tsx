import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  Satellite,
  Waves,
  Radio,
  FileCheck2,
  ShieldCheck,
  ArrowRight,
  Search,
  Activity,
  Database,
  Lock,
  Eye,
  GitBranch,
  BarChart3,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0f1d',
      color: '#f8fafc',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      lineHeight: 1.6,
    }}>
      {/* Navigation Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: 'rgba(10, 15, 29, 0.92)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(51, 65, 85, 0.5)',
        padding: '0.85rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            backgroundColor: '#0284c7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: '0 0 16px rgba(2, 132, 199, 0.4)',
          }}>
            <Compass size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#ffffff' }}>
              Maritime Oil-Spill Attribution Intelligence
            </div>
            <div style={{ fontSize: '0.70rem', color: '#94a3b8', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Environmental Intelligence & Forensic Decision Support
            </div>
          </div>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', fontSize: '0.85rem' }}>
          <button onClick={() => scrollToSection('overview')} style={navLinkStyle}>Overview</button>
          <button onClick={() => scrollToSection('pipeline')} style={navLinkStyle}>Pipeline</button>
          <button onClick={() => scrollToSection('capabilities')} style={navLinkStyle}>Capabilities</button>
          <button onClick={() => scrollToSection('data-sources')} style={navLinkStyle}>Data Sources</button>
          <button onClick={() => scrollToSection('workflow')} style={navLinkStyle}>Workflow</button>
          <button onClick={() => scrollToSection('security')} style={navLinkStyle}>Security</button>
          <button
            onClick={() => navigate('/app')}
            style={{
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              padding: '0.55rem 1.15rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.2s ease',
            }}
          >
            Launch Platform <ArrowRight size={15} />
          </button>
        </nav>
      </header>

      {/* 1. Hero Section */}
      <section style={{
        padding: '5.5rem 2rem 4.5rem',
        maxWidth: '1200px',
        margin: '0 auto',
        textAlign: 'center',
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.85rem',
          backgroundColor: 'rgba(2, 132, 199, 0.12)',
          border: '1px solid rgba(2, 132, 199, 0.35)',
          borderRadius: '20px',
          color: '#38bdf8',
          fontSize: '0.78rem',
          fontWeight: 600,
          marginBottom: '1.75rem',
          letterSpacing: '0.04em',
        }}>
          <ShieldCheck size={14} /> HISTORICAL FORENSIC ATTRIBUTION SYSTEM
        </div>

        <h1 style={{
          fontSize: '3.1rem',
          fontWeight: 800,
          lineHeight: 1.18,
          letterSpacing: '-0.03em',
          color: '#f8fafc',
          maxWidth: '960px',
          margin: '0 auto 1.5rem',
        }}>
          Independent, Explainable Forensic Attribution for Maritime Oil Spills
        </h1>

        <p style={{
          fontSize: '1.15rem',
          color: '#94a3b8',
          maxWidth: '780px',
          margin: '0 auto 2.5rem',
          lineHeight: 1.65,
        }}>
          Reconstruct marine discharge incidents through satellite SAR radar imagery, backward Lagrangian hydrodynamic drift modeling, and spatiotemporal AIS vessel interception. Designed for environmental authorities and maritime investigators.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/app')}
            style={{
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              padding: '0.85rem 1.85rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 18px rgba(2, 132, 199, 0.35)',
            }}
          >
            Launch Forensic Workspace <ArrowRight size={18} />
          </button>
          <button
            onClick={() => scrollToSection('pipeline')}
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.7)',
              color: '#cbd5e1',
              border: '1px solid #334155',
              padding: '0.85rem 1.65rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
            }}
          >
            Explore Scientific Pipeline
          </button>
        </div>
      </section>

      {/* 2. Product Overview Section */}
      <section id="overview" style={sectionWrapperStyle}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>PRODUCT OVERVIEW</div>
          <h2 style={sectionTitleStyle}>Decision Support for Environmental Forensics</h2>
          <p style={sectionSubtitleStyle}>
            A specialized decision-support platform providing objective, mathematical attribution intelligence without speculative legal accusations.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><FileCheck2 size={22} color="#38bdf8" /></div>
            <h3 style={cardTitleStyle}>Forensic Decision Support</h3>
            <p style={cardTextStyle}>
              The system serves as an investigative aid for maritime agencies, coast guards, and environmental regulators. Attribution rankings are accompanied by complete mathematical evidence and uncertainty bounds.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><GitBranch size={22} color="#10b981" /></div>
            <h3 style={cardTitleStyle}>Verifiable Evidence Chain</h3>
            <p style={cardTextStyle}>
              Every attribution score is decomposed into five verifiable factors: spatiotemporal proximity, trajectory drift alignment, vessel risk profile, navigational anomalies, and AIS transponder continuity.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><Eye size={22} color="#a855f7" /></div>
            <h3 style={cardTitleStyle}>Transparent Scientific Integrity</h3>
            <p style={cardTextStyle}>
              Sensor observations are strictly decoupled from model-derived estimates and assumptions. Results are communicated via probability distributions rather than false coordinate certainties.
            </p>
          </div>
        </div>
      </section>

      {/* 3. How the Intelligence Pipeline Works */}
      <section id="pipeline" style={{ ...sectionWrapperStyle, backgroundColor: '#0c1322' }}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>FORENSIC ARCHITECTURE</div>
          <h2 style={sectionTitleStyle}>How the Intelligence Pipeline Works</h2>
          <p style={sectionSubtitleStyle}>
            Every investigation strictly executes through seven deterministic data processing phases.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '900px', margin: '0 auto' }}>
          {[
            { step: '01', title: 'SAR Imagery Acquisition', desc: 'Sentinel-1 C-band synthetic aperture radar imagery is ingested and calibrated.', icon: Satellite },
            { step: '02', title: 'Slick Detection & Lookalike Classification', desc: 'CFAR adaptive thresholding isolates dark patches and rejects low-wind calm water lookalikes.', icon: Search },
            { step: '03', title: 'Backward Hydrodynamic Drift Simulation', desc: 'Monte Carlo particle back-tracking combines CMEMS ocean currents and ERA5 surface winds.', icon: Waves },
            { step: '04', title: 'Origin Estimation & Release Window', desc: 'Dispersion envelope calculates the probable discharge centroid and time window.', icon: Activity },
            { step: '05', title: 'AIS Vessel Interception & Interpolation', desc: 'Regional vessel tracks are filtered and interpolated across the estimated release envelope.', icon: Radio },
            { step: '06', title: 'Multi-Factor Attribution Scoring', desc: 'Five-factor forensic scoring matrix calculates explainable proximity and anomaly indices.', icon: BarChart3 },
            { step: '07', title: 'Evidentiary Dossier Export', desc: 'Audit-ready PDF and JSON evidence packages are compiled with cryptographic SHA-256 validation.', icon: FileCheck2 },
          ].map((item, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1.25rem',
              backgroundColor: '#131b2e',
              border: '1px solid #1e293b',
              padding: '1.25rem 1.5rem',
              borderRadius: '8px',
            }}>
              <div style={{
                fontSize: '1.1rem',
                fontWeight: 800,
                color: '#0284c7',
                fontFamily: 'monospace',
                minWidth: '32px',
              }}>
                {item.step}
              </div>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '6px',
                backgroundColor: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
                flexShrink: 0,
              }}>
                <item.icon size={20} />
              </div>
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.2rem' }}>
                  {item.title}
                </div>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  {item.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Capabilities Section */}
      <section id="capabilities" style={sectionWrapperStyle}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>TECHNICAL CAPABILITIES</div>
          <h2 style={sectionTitleStyle}>Core Forensic Capabilities</h2>
          <p style={sectionSubtitleStyle}>
            Rigorous mathematical and physical engines built for precision maritime analysis.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
          {[
            { title: 'Adaptive CFAR Detection', desc: 'Constant False Alarm Rate spatial windowing isolates oil slicks under variable sea clutter.' },
            { title: 'Monte Carlo Drift Swarms', desc: 'Simulates 200 to 1,000+ stochastic particles driven by oceanographic advection and turbulent diffusion.' },
            { title: 'Spline Waypoint Interpolation', desc: 'High-frequency cubic trajectory interpolation accounts for non-uniform AIS transmission intervals.' },
            { title: 'CPA Distance Computation', desc: 'Calculates Closest Point of Approach relative to the dispersion envelope at the discharge timestamp.' },
            { title: 'AIS Anomaly Detection', desc: 'Automatically flags suspicious transponder gaps, speed drops, and course alterations.' },
            { title: 'Calibrated Uncertainty', desc: 'Conveys geographic dispersion radiuses and temporal confidence intervals.' },
          ].map((cap, i) => (
            <div key={i} style={{ ...cardStyle, padding: '1.35rem' }}>
              <h3 style={{ ...cardTitleStyle, fontSize: '0.95rem' }}>{cap.title}</h3>
              <p style={{ ...cardTextStyle, fontSize: '0.80rem' }}>{cap.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Data Sources Section */}
      <section id="data-sources" style={{ ...sectionWrapperStyle, backgroundColor: '#0c1322' }}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>DATA PROVENANCE</div>
          <h2 style={sectionTitleStyle}>Multi-Source Sensor Integration</h2>
          <p style={sectionSubtitleStyle}>
            Direct ingestion from established European and global earth observation and maritime monitoring infrastructures.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
          <div style={cardStyle}>
            <div style={{ ...iconBoxStyle, backgroundColor: '#0284c715' }}><Satellite size={22} color="#38bdf8" /></div>
            <div style={{ fontSize: '0.70rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.35rem' }}>SAR SATELLITE</div>
            <h3 style={cardTitleStyle}>Copernicus Sentinel-1</h3>
            <p style={cardTextStyle}>
              Level-1 Ground Range Detected (GRD) C-band radar backscatter imagery providing day/night, all-weather ocean surface observation.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={{ ...iconBoxStyle, backgroundColor: '#10b98115' }}><Radio size={22} color="#10b981" /></div>
            <div style={{ fontSize: '0.70rem', fontWeight: 700, color: '#10b981', marginBottom: '0.35rem' }}>VESSEL TELEMETRY</div>
            <h3 style={cardTitleStyle}>AIS Transponder Feeds</h3>
            <p style={cardTextStyle}>
              Terrestrial receiver networks and satellite constellations recording vessel MMSI, GPS waypoints, speed over ground, and course.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={{ ...iconBoxStyle, backgroundColor: '#38bdf815' }}><Waves size={22} color="#38bdf8" /></div>
            <div style={{ fontSize: '0.70rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.35rem' }}>HYDRODYNAMICS</div>
            <h3 style={cardTitleStyle}>CMEMS GLORYS12V1</h3>
            <p style={cardTextStyle}>
              Copernicus Marine Service global ocean physics reanalysis grids providing eastward ($U$) and northward ($V$) surface current velocities.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={{ ...iconBoxStyle, backgroundColor: '#f59e0b15' }}><Activity size={22} color="#f59e0b" /></div>
            <div style={{ fontSize: '0.70rem', fontWeight: 700, color: '#f59e0b', marginBottom: '0.35rem' }}>METEOROLOGY</div>
            <h3 style={cardTitleStyle}>ECMWF ERA5 Winds</h3>
            <p style={cardTextStyle}>
              European Centre for Medium-Range Weather Forecasts atmospheric reanalysis 10-meter surface wind vectors for leeway calculations.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Investigation Workflow Section */}
      <section id="workflow" style={sectionWrapperStyle}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>INVESTIGATION LIFECYCLE</div>
          <h2 style={sectionTitleStyle}>Structured Forensic Workflow</h2>
          <p style={sectionSubtitleStyle}>
            From initial satellite sighting to final court-grade intelligence dossier.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {[
            { phase: 'Phase 1', title: 'Case Setup', desc: 'Define geographic bounds and incident observation time.' },
            { phase: 'Phase 2', title: 'Data Upload', desc: 'Ingest SAR imagery, AIS CSV tracks, and weather grids.' },
            { phase: 'Phase 3', title: 'Advection Drift', desc: 'Reconstruct reverse particle trajectory to estimate spill origin.' },
            { phase: 'Phase 4', title: 'Attribution', desc: 'Score all candidate vessels passing through the discharge window.' },
            { phase: 'Phase 5', title: 'Audit Export', desc: 'Export verifiable forensic report with complete evidence lineage.' },
          ].map((w, idx) => (
            <div key={idx} style={{
              backgroundColor: '#111827',
              border: '1px solid #1e293b',
              padding: '1.25rem',
              borderRadius: '8px',
              borderTop: '3px solid #0284c7',
            }}>
              <span style={{ fontSize: '0.70rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.04em' }}>{w.phase}</span>
              <h4 style={{ fontSize: '0.90rem', fontWeight: 700, color: '#f8fafc', margin: '0.4rem 0 0.35rem' }}>{w.title}</h4>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>{w.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 7. Evidence & Explainability */}
      <section style={{ ...sectionWrapperStyle, backgroundColor: '#0c1322' }}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>OBJECTIVE TRANSPARENCY</div>
          <h2 style={sectionTitleStyle}>Evidence & Explainability</h2>
          <p style={sectionSubtitleStyle}>
            Forensic decision support requires complete clarity on how every conclusion was reached.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.85rem' }}>
              <div style={bulletIconStyle}><CheckIcon /></div>
              <div>
                <strong style={{ color: '#f8fafc', fontSize: '0.90rem' }}>Non-Accusatory Forensic Phrasing</strong>
                <p style={{ color: '#94a3b8', fontSize: '0.80rem', marginTop: '0.2rem' }}>
                  The platform outputs objective, evidence-based statements: "This vessel is the highest-ranked candidate based on available evidence," avoiding unwarranted accusations of guilt.
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.85rem' }}>
              <div style={bulletIconStyle}><CheckIcon /></div>
              <div>
                <strong style={{ color: '#f8fafc', fontSize: '0.90rem' }}>Transparent Factor Weighting</strong>
                <p style={{ color: '#94a3b8', fontSize: '0.80rem', marginTop: '0.2rem' }}>
                  Proximity (35%), Drift Alignment (25%), Vessel Profile (15%), Navigational Anomaly (15%), and AIS Integrity (10%) are individually reported.
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.85rem' }}>
              <div style={bulletIconStyle}><CheckIcon /></div>
              <div>
                <strong style={{ color: '#f8fafc', fontSize: '0.90rem' }}>Evidence Taxonomy</strong>
                <p style={{ color: '#94a3b8', fontSize: '0.80rem', marginTop: '0.2rem' }}>
                  Facts are partitioned into Supporting, Contradicting, Exculpatory, and Uncertainty items for court and regulatory review.
                </p>
              </div>
            </div>
          </div>

          <div style={{
            backgroundColor: '#131b2e',
            border: '1px solid #1e293b',
            padding: '1.5rem',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontSize: '0.78rem',
            color: '#cbd5e1',
          }}>
            <div style={{ color: '#64748b', marginBottom: '0.75rem' }}>// FORMAL ATTRIBUTION VERDICT SPECIFICATION</div>
            <div style={{ color: '#38bdf8' }}>{'{'}</div>
            <div style={{ paddingLeft: '1rem' }}>
              <div>"candidate_name": <span style={{ color: '#34d399' }}>"MT NEW DIAMOND"</span>,</div>
              <div>"mmsi": <span style={{ color: '#fbbf24' }}>"371584000"</span>,</div>
              <div>"attribution_score": <span style={{ color: '#f87171' }}>95.8</span>,</div>
              <div>"risk_level": <span style={{ color: '#f87171' }}>"VERY_HIGH"</span>,</div>
              <div>"closest_approach_km": <span style={{ color: '#38bdf8' }}>0.082</span>,</div>
              <div>"discharge_window_cpa": <span style={{ color: '#a855f7' }}>true</span>,</div>
              <div>"ais_gap_detected": <span style={{ color: '#f87171' }}>true</span>,</div>
              <div>"verdict_statement": <span style={{ color: '#94a3b8' }}>"This vessel is the highest-ranked candidate..."</span></div>
            </div>
            <div style={{ color: '#38bdf8' }}>{'}'}</div>
          </div>
        </div>
      </section>

      {/* 8. Environmental Intelligence */}
      <section style={sectionWrapperStyle}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>PHYSICAL DYNAMICS</div>
          <h2 style={sectionTitleStyle}>Environmental Hydrodynamics</h2>
          <p style={sectionSubtitleStyle}>
            Oil drift is governed by ocean surface currents, atmospheric wind leeway, and stochastic turbulent diffusion.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Lagrangian Advection Formula</h3>
            <p style={cardTextStyle}>
              Particles are advected backwards combining hydrodynamic surface currents and 3% wind leeway:
            </p>
            <div style={{
              fontFamily: 'monospace',
              backgroundColor: '#131b2e',
              padding: '0.65rem 0.85rem',
              borderRadius: '4px',
              fontSize: '0.78rem',
              color: '#38bdf8',
              margin: '0.5rem 0',
            }}>
              x(t - Δt) = x(t) - [ u_current + 0.030 · u_wind + u_turb ] · Δt
            </div>
            <p style={cardTextStyle}>
              where 0.030 is the standard leeway wind drag factor.
            </p>
          </div>
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Monte Carlo Turbulent Perturbation</h3>
            <p style={cardTextStyle}>
              Sub-grid scale ocean turbulence is simulated via stochastic random walks scaled by horizontal diffusivity coefficient Kh = 2.5 m²/s.
            </p>
          </div>
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Calibration & Validation</h3>
            <p style={cardTextStyle}>
              Drift trajectories have been validated against ground truth historical incidents (e.g. MT New Diamond 2020 and Ennore Port 2017) with verified spatial convergence.
            </p>
          </div>
        </div>
      </section>

      {/* 9. Security & Reliability */}
      <section id="security" style={{ ...sectionWrapperStyle, backgroundColor: '#0c1322' }}>
        <div style={sectionHeaderStyle}>
          <div style={sectionEyebrowStyle}>ENTERPRISE GRADE</div>
          <h2 style={sectionTitleStyle}>Security, Reliability & Air-Gap Ready</h2>
          <p style={sectionSubtitleStyle}>
            Engineered for high-security maritime defense, coast guard, and regulatory operations.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><Lock size={20} color="#38bdf8" /></div>
            <h3 style={cardTitleStyle}>Offline & Air-Gapped Deployable</h3>
            <p style={cardTextStyle}>
              Fully operational without an external internet connection using local NetCDF ocean grids and archived AIS datasets.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><ShieldCheck size={20} color="#10b981" /></div>
            <h3 style={cardTitleStyle}>Input Validation & Sanitization</h3>
            <p style={cardTextStyle}>
              Protection against path traversal, archive bombs, and malicious file uploads with strict size limits and MIME validation.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><Database size={20} color="#a855f7" /></div>
            <h3 style={cardTitleStyle}>Deterministic Reproducibility</h3>
            <p style={cardTextStyle}>
              Fixed random seeds and recorded simulation parameters allow identical mathematical replay for court evidence.
            </p>
          </div>
          <div style={cardStyle}>
            <div style={iconBoxStyle}><FileCheck2 size={20} color="#fbbf24" /></div>
            <h3 style={cardTitleStyle}>Cryptographic SHA-256 Hashes</h3>
            <p style={cardTextStyle}>
              Investigation bundles and report outputs are cryptographically sealed to ensure verifiable data integrity.
            </p>
          </div>
        </div>
      </section>

      {/* 10. Call to Action */}
      <section style={{
        padding: '5rem 2rem',
        maxWidth: '900px',
        margin: '0 auto',
        textAlign: 'center',
      }}>
        <div style={{
          backgroundColor: '#111827',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '3.5rem 2.5rem',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginBottom: '1rem' }}>
            Access the Maritime Intelligence Workspace
          </h2>
          <p style={{ fontSize: '1rem', color: '#94a3b8', maxWidth: '600px', margin: '0 auto 2rem' }}>
            Evaluate active marine pollution incidents, inspect satellite SAR slicks, simulate backward particle drift, and rank candidate vessel trajectories.
          </p>
          <button
            onClick={() => navigate('/app')}
            style={{
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              padding: '0.90rem 2.2rem',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '1rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 20px rgba(2, 132, 199, 0.4)',
            }}
          >
            Launch Platform <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* 11. Footer */}
      <footer style={{
        borderTop: '1px solid #1e293b',
        backgroundColor: '#080d1a',
        padding: '2.5rem 2rem',
        fontSize: '0.80rem',
        color: '#64748b',
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div>
            <strong style={{ color: '#cbd5e1' }}>Maritime Oil-Spill Attribution Intelligence</strong>
            <div style={{ marginTop: '0.2rem' }}>
              Decision Support System for Marine Pollution Forensic Investigation
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <span style={{ color: '#94a3b8' }}>Version 0.1.0</span>
            <span style={{ color: '#94a3b8' }}>Universal UTC Timestamps</span>
            <span style={{ color: '#94a3b8' }}>WGS84 EPSG:4326</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Internal reusable CSS objects
const navLinkStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: '#94a3b8',
  cursor: 'pointer',
  fontSize: '0.85rem',
  fontWeight: 500,
  padding: '0.25rem 0',
};

const sectionWrapperStyle: React.CSSProperties = {
  padding: '4.5rem 2rem',
  maxWidth: '1200px',
  margin: '0 auto',
};

const sectionHeaderStyle: React.CSSProperties = {
  textAlign: 'center',
  marginBottom: '3rem',
};

const sectionEyebrowStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  fontWeight: 700,
  letterSpacing: '0.08em',
  color: '#0284c7',
  marginBottom: '0.5rem',
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: '2rem',
  fontWeight: 800,
  letterSpacing: '-0.02em',
  color: '#ffffff',
  margin: '0 0 0.8rem',
};

const sectionSubtitleStyle: React.CSSProperties = {
  fontSize: '1rem',
  color: '#94a3b8',
  maxWidth: '680px',
  margin: '0 auto',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid #1e293b',
  borderRadius: '8px',
  padding: '1.5rem',
};

const cardTitleStyle: React.CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 700,
  color: '#f8fafc',
  margin: '0.5rem 0 0.4rem',
};

const cardTextStyle: React.CSSProperties = {
  fontSize: '0.85rem',
  color: '#94a3b8',
  lineHeight: 1.6,
  margin: 0,
};

const iconBoxStyle: React.CSSProperties = {
  width: '42px',
  height: '42px',
  borderRadius: '8px',
  backgroundColor: '#1e293b',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: '0.85rem',
};

const bulletIconStyle: React.CSSProperties = {
  width: '20px',
  height: '20px',
  borderRadius: '50%',
  backgroundColor: '#0284c720',
  color: '#38bdf8',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: 0,
  marginTop: '0.2rem',
};

const CheckIcon = () => (
  <span style={{ fontSize: '11px', fontWeight: 900 }}>✓</span>
);
