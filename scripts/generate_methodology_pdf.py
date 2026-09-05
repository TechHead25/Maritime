import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#64748b'))
        if self._pageNumber > 1:
            self.drawString(54, 805, 'MARITIME OIL-SPILL ATTRIBUTION INTELLIGENCE (SIH26143)')
            self.drawRightString(541, 805, 'SCIENTIFIC METHODOLOGY & FORENSIC REPORT')
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.setLineWidth(0.5)
            self.line(54, 798, 541, 798)
        self.setStrokeColor(colors.HexColor('#cbd5e1'))
        self.setLineWidth(0.5)
        self.line(54, 45, 541, 45)
        self.drawString(54, 32, 'OFFICMPL DECISION-SUPPORT INTELLIGENCE — NON-ACCUSATORY FORENSICS')
        page_str = f'Page {self._pageNumber} of {page_count}'
        self.drawRightString(541, 32, page_str)
        self.restoreState()

os.makedirs('docs', exist_ok=True)
pdf_path = 'docs/scientific_architecture_and_methodology.pdf'
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=A4,
    leftMargin=54,
    rightMargin=54,
    topMargin=54,
    bottomMargin=54,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0f172a'))
subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=14, textColor=colors.HexColor('#2563eb'))
h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#0f172a'), spaceBefore=12, spaceAfter=5, keepWithNext=True)
h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=colors.HexColor('#1e293b'), spaceBefore=8, spaceAfter=3, keepWithNext=True)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=5)
bullet_style = ParagraphStyle('Bullet', parent=body_style, leftIndent=12, firstLineIndent=-8, spaceAfter=3)
formula_style = ParagraphStyle('Formula', parent=styles['Normal'], fontName='Courier-Bold', fontSize=8.2, leading=11.5, textColor=colors.HexColor('#0f172a'), backColor=colors.HexColor('#f1f5f9'), borderPadding=5, spaceBefore=3, spaceAfter=5)
table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.6, leading=10.5, textColor=colors.HexColor('#1e293b'))
table_header = ParagraphStyle('TableH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.8, leading=10.5, textColor=colors.HexColor('#ffffff'))

story = []
story.append(Paragraph('Maritime Oil-Spill Attribution Intelligence', title_style))
story.append(Spacer(1, 4))
story.append(Paragraph('Scientific Architecture, Hudrodynamic Modeling & Forensic Methodologies', subtitle_style))
story.append(Spacer(1, 6))
story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=6))

meta_data = [
    [Paragraph('<b>Classification:</b> Technical Dossier / Decision Support', table_cell), Paragraph('<b>Version:</b> 1.0 (Production Release)', table_cell)],
    [Paragraph('<b>Problem Statement:</b> SIH26143 - Spatiotemporal Attribution', table_cell), Paragraph(f'<b>Date:</b> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}', table_cell)],
    [Paragraph('<b>Core Paradigm:</b> Lagrangian Inverse Backtracking', table_cell), Paragraph('<b>Application:</b> Decision Support & Maritime Forensics', table_cell)],
]
meta_table = Table(meta_data, colWidths=[240, 247])
meta_table.setStyle(TableStyle([    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story.append(meta_table)
story.append(Spacer(1, 8))

# 1. Executive Overview
story.append(Paragraph('1. Executive Overview & Problem Formulation', h1_style))
story.append(Paragraph(
    'Satellite surveillance detects oil slicks only after they have surfaced and spread across the ocean surface. ' 
    'By the time a satellite observes the slick, ocean currents and winds have transported, deformed, and dispersed the oil miles away from its release location, ' 
    'while the responsible vessel has steamed outside the satellite swath. ' 
    'This platform resolves the <b>Spatiotemporal Inverse Attribution Problem</b>: backtracking an observed synthetic aperture radar (SAR) slick through ' 
    'historical space and time, deriving the origin envelope and release window, and correlating candidate vessel AIS transponder tracks.',
    body_style
))

# 2. Forensic Pipeline
story.append(Paragraph('2. End-to-End Forensic Pipeline Architecture', h1_style))
flow_data = [
    [Paragraph('<b>Stage</b>', table_header), Paragraph('<b>Operational Module</b>', table_header), Paragraph('<b>Inputs & Telemetry</b>', table_header), Paragraph('<b>Analytical Output</b>', table_header)],
    [Paragraph('1', table_cell), Paragraph('SAR Detection', table_cell), Paragraph('Sentinel-1 C-band SAR (OData / GeoTIFF)', table_cell), Paragraph('Adaptive CFAR segmentation, slick polygon, centroid', table_cell)],
    [Paragraph('2', table_cell), Paragraph('Lookalike Screening', table_cell), Paragraph('Morphology + Open-Meteo wind speed', table_cell), Paragraph('Low-wind calms / biogenic slick rejection audit', table_cell)],
    [Paragraph('3', table_cell), Paragraph('Lagrangian Drift', table_cell), Paragraph('Copernicus Marine CMEMS + 10m Wind', table_cell), Paragraph('Backward Monte Carlo particle swarm advection', table_cell)],
    [Paragraph('4', table_cell), Paragraph('Origin Estimation', table_cell), Paragraph('Particle ensemble spatial density', table_cell), Paragraph('Origin centroid, dispersion cloud covariance', table_cell)],
    [Paragraph('5', table_cell), Paragraph('Release Windowing', table_cell), Paragraph('Fay weathering spreading kinetics', table_cell), Paragraph('Spill release window [T_min, T_max]', table_cell)],
    [Paragraph('6', table_cell), Paragraph('AIS Interception', table_cell), Paragraph('Historical/Live AIS GPS streams', table_cell), Paragraph('Waypoint interpolation, AIS blackout gap detection', table_cell)],
    [Paragraph('7', table_cell), Paragraph('Attribution Scoring', table_cell), Paragraph('Spatiotemporal distance matrices', table_cell), Paragraph('Ranked candidate leaderboard & forensic dossier', table_cell)],
]
flow_table = Table(flow_data, colWidths=[25, 105, 175, 182])
flow_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMOADDING', (0,0), (-1,-1), 3),
]))
story.append(flow_table)
story.append(Spacer(1, 8))

# 3. SAR Detection
story.append(Paragraph('3. SAR Slick Detection & Lookalike Discrimination', h1_style))
story.append(Paragraph(
    '<b>Physical Principle:</b> Hydrocarbon films dampen capillary and short gravity waves on the sea surface, dramatically suppressing radar backscatter. '
    'Consequently, in Sentinel-1 Synthetic Aperture Radar (SAR) backscatter imagery, oil slicks appear as dark anomalies contrasted against the background ocean.',
    body_style
))
story.append(Paragraph('<b>Constant False Alarm Rate (CFAR) Adaptive Thresholding:</b>', h2_style))
story.append(Paragraph(
    'To handle varying sea states across wide satellite swaths, CFAR dynamically calculates local thresholds:',
    body_style
))
story.append(Paragraph('T(x, y) = &mu;_b(x, y) - k &middot; &sigma;_b(x, y)', formula_style))
story.append(Paragraph(
    'where &mu;_b is the local background mean backscatter, &sigma;_b is the background standard deviation, and k is a sensitivity multiplier (typically 2.0 to 3.0).',
    body_style
))
story.append(Paragraph('<b>Feature Extraction & Lookalike Rejection:</b>', h2_style))
story.append(Paragraph('&bull; <b>Elongation Ratio:</b> E = L_major / L_minor. Slicks resulting from moving vessels exhibit high elongation (E &ge; 3.0).', bullet_style))
story.append(Paragraph('&bull; <b>Isoperimetric Quotient (Circularity):</b> Q = 4&pi;A / P^2. Rejects irregular natural calm areas and broad biogenic slicks.', bullet_style))
story.append(Paragraph('&bull; <b>Wind-Speed Thresholding:</b> Slicks observed in wind regimes below 2.0 m/s (natural calm lookalikes) or above 12.0 m/s (high dispersion) are rejected.', bullet_style))

# 4. Backward Lagrangian Drift
story.append(PageBreak())
story.append(Paragraph('4. Backward Lagrangian Hydrodynamic Drift Engine', h1_style))
story.append(Paragraph(
    'Following slick detection at satellite acquisition time T_SAR, the engine initializes a Monte Carlo particle swarm ' 
    '(N = 1,000 to 5,000 virtual particles) across the segmented polygon. The ensemble is integrated backwards in time with negative time increments (&Delta;t = -30 min):',
    body_style
))
story.append(Paragraph('<b>Governing Advection-Diffusion Equation:</b>', h2_style))
story.append(Paragraph('x_i(t - &Delta;t) = x_i(t) - [ &alpha; &middot; u_current(x, t) + &gamma; &middot; R(&theta;) &middot; w_10(x, t) ] &Delta;t + &eta;_i(t)', formula_style))
story.append(Paragraph('&bull; <b>Ocean Current Advection (u_current):</b> Copernicus Marine (CMEMS / HYCOM) surface velocity vectors. Scaling coefficient &alpha; = 1.00.', bullet_style))
story.append(Paragraph('&bull; <b>Atmospheric Wind Leeway (w_10):</b> Open-Meteo Marine Global NWP 10-meter wind vectors. Empirical leeway factor &gamma; = 0.03 (3.0%).', bullet_style))
story.append(Paragraph('&bull; <b>Coriolis Leeway Deflection (R(&theta;)):</b> Rotational deflection angle &theta; (Ekman spiral) accounted for according to hemisphere.', bullet_style))
story.append(Paragraph('&bull; <b>Turbulent Eddy Diffusion (&eta;_i):</b> Stochastic Brownian perturbation modeling ocean sub-grid turbulence:', bullet_style))
story.append(Paragraph('&Delta;x_turbulent = R_norm &middot; sqrt(2 &middot; K_h &middot; &Delta;t)', formula_style))
story.append(Paragraph('where K_h is the horizontal eddy diffusivity (2.5 to 10.0 m^2/s) and R_norm is a standard Gaussian random vector N(0, 1) seeded deterministically.', body_style))

# 5. Origin Estimation
story.append(Paragraph('5. Spatiotemporal Uncertainty Envelope & Release Window', h1_style))
story.append(Paragraph(
    'The platform avoids static coordinates, expressing the origin as a <b>Probability Dispersion Cloud</b> at each historical timestep;',
    body_style
))
story.append(Paragraph('&sigma; = sqrt( (1 / N) &Sigma; || x_i - &mu; ||^2 )', formula_style))
story.append(Paragraph(
    '<b>Release Window Estimation:</b> Based on Fay\'s empirical three-phase spreading kinetics and weathering models (evaporation and emulsification), ' 
    'the physical age of the slick is constrained to an interval [T_spill,min, T_spill,max], establishing the time window for vessel intersection.',
    body_style
))

# 6. AIS Interception
story.append(Paragraph('6. AIS Vessel Track Interception & Gap Analysis', h1_style))
story.append(Paragraph(
    'AIS transponder telemetry within the spatial-temporal envelope is ingested and interpolated along spherical geodesic tracks using the Great-Circle Haversine formula:',
    body_style
))
story.append(Paragraph('d = 2R &middot; arcsin( sqrt( sin^2(&Delta;&phi;/2) + cos(&phi;_1) &middot; cos(&phi;_2) &middot; sin^2(&Delta;&lambda;/2) ) )', formula_style))
story.append(Paragraph(
    '<b>Dark Vessel & AIS Gap Detection:</b> Transponder blackouts exceeding 45 minutes across the spill origin corridor are flagged as anomaly gaps (&Delta;t_gap), ' 
    'penalizing the vessel\'s continuity score.',
    body_style
))

# 7. Attribution Scoring
story.append(PageBreak())
story.append(Paragraph('7. Multi-Factor Attribution Scoring Matrix', h1_style))
story.append(Paragraph(
    'Attribution is synthesized into a calibrated composite score (0 to 100 points) evaluating four independent forensic pillars:',
    body_style
))
story.append(Paragraph('Attribution Score = w_1 &middot; S_proximity + w_2 &middot; S_temporal + w_3 &middot; S_relevance + w_4 &middot; S_continuity', formula_style))

score_data = [
    [Paragraph('<b>Factor</b>', table_header), Paragraph('<b>Weight</b>', table_header), Paragraph('<b>Formula / Definition</b>', table_header), Paragraph('<b>Forensic Rationale</b>', table_header)],
    [
        Paragraph('Spatial Proximity (S_prox)', table_cell),
        Paragraph('<b>35%</b>', table_cell),
        Paragraph('S_prox = max(0, 100 &middot; (1 - d_min / R_threshold))<br/>where R_threshold = 25 km', table_cell),
        Paragraph('Closest point of approach (CPA) between vessel trajectory and backward drift probability centroid.', table_cell)
    ],
    [
        Paragraph('Temporal Coincidence (S_time)', table_cell),
        Paragraph('<b>30%</b>', table_cell),
        Paragraph('S_time = 100 &middot; exp(-(&Delta;t_passage - t_release)^2 / (2 &middot; &sigma;_t^2))', table_cell),
        Paragraph('Evaluates overlap between vessel transit time and the scientifically derived release window.', table_cell)
    ],
    [
        Paragraph('Vessel Relevance (S_vessel)', table_cell),
        Paragraph('<b>20%</b>', table_cell),
        Paragraph('Crude/Product Tanker: 95-100<br/>Chemical/Bulk Carrier: 70-85<br/>Cargo/Container: 50-65<br/>Fishing/Pleasure: 10-25', table_cell),
        Paragraph('Risk classification based on cargo carrying capacity, bunker fuel type, and historical spill potential.', table_cell)
    ],
    [
        Paragraph('AIS Continuity (S_cont)', table_cell),
        Paragraph('<b>15%</b>', table_cell),
        Paragraph('Continuous transmission: 100<br/>Minor telemetry jitter (&lt;45m): 85<br/>Unexplained gap across spill origin: 20', table_cell),
        Paragraph('Penalizes deliberate transponder shutdowns, track spoofing, or irregular maneuvers near origin.', table_cell)
    ],
]
score_table = Table(score_data, colWidths=[95, 45, 175, 172])
score_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
    ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story.append(score_table)
story.append(Spacer(1, 10))

# 8. Forensic Integrity
story.append(Paragraph('8. Forensic Integrity & Legal Safeguards', h1_style))
story.append(Paragraph(
    'To guarantee admissibility and evidentiary defensibility before maritime tribunals and international bodies:',
    body_style
))
story.append(Paragraph('&bull; <b>Non-Accusatory Wording:</b> The platform never issues automated verdicts of legal guilt. Reports state: <i>&quot;Candidate vessel [Name] (MMSI: [X]) is the highest-ranked candidate based on available spatiotemporal, hydrodynamic, and AIS evidence.&quot;</i>', bullet_style))
story.append(Paragraph('&bull; <b>Strict Anti-Fabrication Rule:</b> When external sensor providers are unconfigured, the system reports UNCONFIGURED honestly. Synthetic fallbacks in production are strictly forbidden.', bullet_style))
story.append(Paragraph('&bull; <b>Immutable Provenance Audit Trail:</b> Every analysis step records sensor platform IDs, acquisition timestamps, grid parameters, and SHA-256 hashes of input rasters in an immutable audit chain.', bullet_style))
story.append(Paragraph('&bull; <b>Decision-Support Dossier:</b> Results compile directly into exportable technical dossiers embedding cartographic overlays, score breakdowns, lookalike rejection logs, and sensor limitation disclosures.', bullet_style))


doc.build(story, canvasmaker=NumberedCanvas)
print('SUCCESS_PDF_GENERATED')
