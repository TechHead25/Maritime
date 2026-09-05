# 5-Minute SIH Live Demonstration Script

**Project:** Maritime Oil-Spill Attribution Intelligence (SIH26143)  
**Target Audience:** Smart India Hackathon Jury & Technical Evaluators  
**Duration:** Exactly 5 Minutes  
**Core Storyline:** Slick (SAR) $\longrightarrow$ Drift (CMEMS/ERA5) $\longrightarrow$ Origin (Lagrangian) $\longrightarrow$ Vessels (AIS) $\longrightarrow$ Evidence $\longrightarrow$ Ranking $\longrightarrow$ Official Dossier  

---

## ⏱ Minute-by-Minute Live Presentation Guide

### 🎬 Minute 0:00 – 0:45 | The Maritime Attribution Challenge
**What to Show on Screen:**  
The main dashboard homepage with the top header: *"Maritime Oil-Spill Attribution Intelligence"*.

**What to Say:**
> *"Respected Judges, illegal and accidental maritime oil spills cause devastating ecological harm along our coastlines. While satellite radar (SAR) can detect oil slicks day and night, identifying the vessel responsible has historically been nearly impossible.*
> 
> *By the time a satellite observes a slick, ocean currents and winds have moved it kilometers away from where it was discharged. Furthermore, rogue vessels intentionally disable their AIS transponders.*
> 
> *Our platform solves this with a deterministic, physics-based forensic decision-support pipeline. Today, we demonstrate this using the real historical incident of the crude oil tanker MT New Diamond off the coast of Sri Lanka."*

---

### 🛰️ Minute 0:45 – 1:30 | Step 1 & 2: SAR Ingestion & Slick Detection
**What to Click:**  
Click the green button: **`▶ Start Guided Demo Investigation`** at the top of the dashboard.

**What to Say:**
> *"With a single action, our investigation begins. In Step 1, the platform ingests a calibrated Copernicus Sentinel-1A Synthetic Aperture Radar swath acquired at 12:30 UTC.*
> 
> *In Step 2, our CFAR dark-patch segmentation and adaptive 5x5 speckle filter detect a 4.8 square kilometer mineral oil slick at 7.90°N, 82.95°E. The detector automatically eliminates false alarms like low-wind calm water and coastal land shadows with transparent audit logs."*

---

### 🌊 Minute 1:30 – 2:30 | Step 3, 4 & 5: Backward Drift & Origin Reconstruction
**What to Show on Screen:**  
The map auto-advances to Steps 3, 4, and 5, showing the cyan backward drift envelopes and the origin star marker.

**What to Say:**
> *"Now we solve the inverse transport problem. In Step 3, our Lagrangian drift engine advects 1,000 Monte Carlo particles 18 hours backward in time using Copernicus CMEMS hydrodynamic surface currents and ERA5 surface winds with turbulent diffusion.*
> 
> *In Step 4, the particle cloud reconstructs the probable origin at 7.78°N, 82.72°E with a 1-sigma dispersion uncertainty of 0.58 kilometers.*
> 
> *In Step 5, the release window model brackets the exact discharge between 01:00 and 05:00 UTC, peaking at 03:15 UTC—9.25 hours before satellite acquisition."*

---

### 🚢 Minute 2:30 – 3:30 | Step 6 & 7: AIS Telemetry & Candidate Interception
**What to Show on Screen:**  
Steps 6 and 7 reveal the 5 regional vessel tracks and the ranked candidate leaderboard on the right column.

**What to Say:**
> *"In Step 6, the system queries historical AIS tracking logs for all regional vessels. Between discrete GPS pings, we interpolate vessel trajectories along geodesic paths.*
> 
> *In Step 7, candidate interception filters vessels that intersected the origin envelope during the release window. The crude tanker MT NEW DIAMOND is immediately identified as the closest candidate, passing within 7.8 kilometers of the reconstructed origin centroid."*

---

### 📊 Minute 3:30 – 4:15 | Step 8 & 9: Explainable 5-Factor Attribution & Evidence
**What to Click:**  
Click on the **MT NEW DIAMOND** candidate card in the right column to showcase the Score Breakdown and Evidence Cards.

**What to Say:**
> *"Unlike black-box AI, our 5-Factor Attribution Engine is 100% transparent and explainable:*
> 1. *Proximity (38.2 / 40 pts) for intersecting the drift envelope.*
> 2. *Trajectory Alignment (24.1 / 25 pts) matching the monsoon slick axis.*
> 3. *Navigational Anomaly (13.5 / 15 pts) for a severe speed drop from 14.2 knots down to 0.4 knots.*
> 4. *Vessel Risk (8.0 / 10 pts) as a high-risk laden crude carrier.*
> 5. *AIS Integrity (9.0 / 10 pts) for a 5.1-hour transponder blackout right during the release window.*
> 
> *Total Score: 87.7/100 (HIGH RISK). In compliance with maritime legal standards, our system provides decision support and never issues an automated accusation."*

---

### 📥 Minute 4:15 – 5:00 | One-Click Official PDF Dossier & Wrap-Up
**What to Click:**  
Click the **`📥 Export Report (PDF)`** button in the case header bar. Open the generated PDF report.

**What to Say:**
> *"Finally, investigators can click 'Export Report' to instantly generate this official 3-page Maritime Oil-Spill Investigation Report.*
> 
> *It includes complete data provenance tables, embedded high-resolution SAR and Lagrangian drift figures, candidate ranking matrices, itemized evidence chains, rejected lookalike logs, and technical limitations.*
> 
> *Our entire backend pipeline executes in just 114 milliseconds with 100% deterministic reproducibility. Thank you, and we look forward to your questions."*

---

## 🎯 Presenter Quick Cheat-Sheet

| Trigger Action | Visual Feedback on Screen | Key Talking Point |
|---|---|---|
| **Click `▶ Start Guided Demo`** | Stepper begins auto-advancing from Step 1 to 9 | Single-click end-to-end guided walkthrough |
| **Hover on Reconstructed Origin** | Star marker with $0.58\text{ km}$ uncertainty ring | Inverse Lagrangian advection against CMEMS currents |
| **Select MT NEW DIAMOND** | Score bars and Evidence Cards illuminate | 14.2 to 0.4 kts speed drop + 5.1h AIS blackout |
| **Click `📥 Export Report (PDF)`** | Downloads official 3-page investigation report | Official decision-support dossier ready for maritime authorities |
| **Click `🔄 Reset Demo`** | Workspace resets to initial baseline state | Ready for another clean live demonstration |
