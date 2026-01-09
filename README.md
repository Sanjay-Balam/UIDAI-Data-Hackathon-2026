# Implementation Plan - UIDAI Data Hackathon 2026

# Project Narrative: "Aadhaar Pulse 2.0"

> **Narrative**: "Aadhaar Pulse 2.0 moves beyond availability to measure **adequacy**. By analyzing the 'Stress' on the ecosystem and the 'Risk' to the child lifecycle, we provide UIDAI with a predictive operational roadmap."

## The Three Pillars (Expert Refined)

### Pillar 1: Service Accessibility Index (SAI)
*   **The Reality**: Centers exist, but are they swamped? We measure **Adequacy**, not just availability.
*   **Metric**: **Service Pressure Score (SPS)**.
    *   *Concept Formula*: `Projected Demand / Service Capacity`.
    *   *Implementation*: Since we lack "Kit" counts, we use **`Transaction Volume / Active PIN Codes`** as a proxy. High volume per PIN = High Stress (Queue Crisis).
*   **Winning Argument**: "UIDAI measures Availability (is there a center?), but my model measures Adequacy (can it handle the load?)."

### Pillar 2: Child Lifecycle Compliance Score (CLCS)
*   **The Reality**: 17 Crore children have pending Mandatory Biometric Updates (MBU), creating a "ticking time bomb" of ID inactivation.
*   **Metric**: **Child Risk Score (CRS)**.
    *   *Components*:
        1.  **The Backlog**: Ratio of `bio_age_5_17` updates vs `age_0_5` historical enrolments.
        2.  **The "Ghost" Factor**: Identifying districts with low 0-5 enrolment saturation (Ghost Children).
*   **Winning Argument**: "Current updates are reactive. My model makes them proactive—predicting who turns 5/15 next month to prevent exclusion."

### Pillar 3: Demand Intensity Heatmap (DIH)
*   **The Reality**: Demand is seasonal (School Rush), but supply is static.
*   **Metric**: **Velocity & Rejection Intensity**.
    *   *Analysis*: Identify "School Rush" spikes (June-Aug) and anomalies in `rejected` applications (if data permits) or extreme volume spikes.
*   **Winning Argument**: "Static resources cannot solve dynamic problems. This Heatmap tells you exactly where to move 'Mobile Aadhaar Vans' *before* the queue starts."

## Phase 2: Critical Improvements (The "Expert" Polish)
Based on your feedback, we are adding a rigor layer:

### 1. Data Hygiene (The Foundation)
*   **Problem**: Garbage data (`?', '100000'`) and inconsistent spellings (`Ahmednagar` vs `Ahmadnagar`) skew results.
*   **Fix**: Implement `normalize_districts()` function to clean string variations and drop numeric/invalid rows.

### 2. Logic Correction (The CLCS Formula)
*   **Problem**: Comparing `Bio Updates` (Age 5-17) to `New Enrolments` (Age 0-5) is a cohort mismatch.
*   **Fix**: New Formula = `Bio Updates (5-17) / Total Child Activity (0-17)`. This represents the "Share of Children Vitality". Low share = Dormant/At-risk population.

### 3. State-Level Intelligence
*   **Problem**: District view is too granular for national policy.
*   **Fix**: Aggregate `SPS` and `CRS` to the **State Level** to answer: "Which State is the biggest bottleneck?"

### 4. Visual Impact
*   **Additions**:
    *   **India Choropleth**: State-wise heat map.
    *   **Trend Compounding**: Time-series line charts to show growth velocity.

## Technology Stack
*   **Data Analysis**: Python (Pandas)
*   **Visualization**: Plotly (Interactive Maps & Charts)
*   **Output Format**: HTML Reports & Consolidated PDF

## Project Structure
*   `src/`: Source code for data loading and analysis.
*   `visualizations/`: Generated HTML charts.
*   `aadhaar_pulse_analysis.csv`: Processed analytical dataset.
*   `WALKTHROUGH.md`: Guide to interpreting the results.
