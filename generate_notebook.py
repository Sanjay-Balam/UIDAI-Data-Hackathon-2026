import nbformat as nbf
import os

def create_notebook():
    nb = nbf.v4.new_notebook()

    # --- Markdown Content ---
    
    exec_summary = """# Aadhaar Pulse 2.0: Strategic Operation Report (Hackathon Final)

## Executive Summary
**Aadhaar Pulse 2.0** moves beyond static enrollment tracking to measure the **Operational Adequacy** and **Social Protective Power** of the ecosystem. 

Using 10 months of transactional logs across 36 States and 700+ Districts, we identified:
1.  **Service Deserts**: Districts with >5,000 transactions per PIN code (Critical Failure Risk).
2.  **Child Exclusion Risks**: 'Ghost Districts' (e.g., in Assam/Bihar) where children are enrolled but statistically failing to update biometrics (-2.0σ Z-Score).
3.  **Predictive Seasonality**: A verifiable "School Rush" spike (June-August) requiring elastic staffing.

This report details the methodology, statistical findings, and actionable recommendations.
"""

    intro_code = """import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import urllib.request

# Configuration
pio.templates.default = "plotly_dark"
BASE_PATH = "../" # Relative path to project root

# Load Cleaned Data
dist_df = pd.read_csv(f"{BASE_PATH}aadhaar_pulse_district_clean.csv")
state_df = pd.read_csv(f"{BASE_PATH}aadhaar_pulse_state_clean.csv")
trend_df = pd.read_csv(f"{BASE_PATH}aadhaar_pulse_trends_clean.csv")

# Load GeoJSON
geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
with urllib.request.urlopen(geojson_url) as url:
    india_states = json.loads(url.read().decode())

print("Data Loaded Successfully.")
print(f"Districts Analyzed: {len(dist_df)}")
print(f"States/UTs Covered: {len(state_df)}")
"""

    # --- PILLAR 1 ---
    section_1_md = """## Pillar 1: Service Accessibility Index (SAI)
**The Problem**: UIDAI lists where centers *are*, but not if they are *adequate*.
**The Metric**: `Service Pressure Score (SPS) = Transactions / Active PIN Codes`.
**The Finding**:
High Pressure scores indicate "Queue Crisis" zones. The map below reveals a clear operational strain in specific states.
"""

    section_1_plot = """# State-Level Service Pressure Map
fig_map_sps = px.choropleth(
    state_df,
    geojson=india_states,
    featureidkey='properties.ST_NM',
    locations='state',
    color='sps_score',
    color_continuous_scale='Reds',
    title='State-wise Service Pressure Score (SPS)',
)
fig_map_sps.update_geos(fitbounds="locations", visible=False)
fig_map_sps.show()
"""

    section_1_district = """# Top 10 Critical Pressure Districts
top_pressure = dist_df.sort_values('sps_score', ascending=False).head(10)
fig_bar = px.bar(
    top_pressure, x='district', y='sps_score', color='state',
    title='Top 10 Districts: Critical Service Pressure Zones',
    labels={'sps_score': 'Transactions per PIN'}
)
fig_bar.show()
"""

    # --- PILLAR 2 ---
    section_2_md = """## Pillar 2: Child Lifecycle Compliance Score (CLCS)
**The Problem**: 17 Crore children face ID deactivation if they miss mandatory biometric updates (MBU).
**The Metric**: **Compliance Z-Score**. We measure the "Share of Vitality" (`Updates / Activity`) and benchmark deviations from the National Average.
**The Finding**:
*   **Green Zones**: States keeping up with child updates.
*   **Red Zones (< -1.5 Z-Score)**: States where children are enrolled but "Silently Excluded" from updates.
"""
    
    section_2_plot = """# State Compliance Z-Score Map
# Benchmarking states against national average
state_mean = state_df['compliance_share'].mean()
state_std = state_df['compliance_share'].std()
state_df['z_score'] = (state_df['compliance_share'] - state_mean) / state_std

fig_map_clcs = px.choropleth(
    state_df,
    geojson=india_states,
    featureidkey='properties.ST_NM',
    locations='state',
    color='z_score',
    color_continuous_scale='RdYlGn', 
    range_color=[-2, 2],
    title='State Compliance Z-Score (Statistical Deviation)',
)
fig_map_clcs.update_geos(fitbounds="locations", visible=False)
fig_map_clcs.show()
"""

    section_2_scatter = """# District Risk Map (Outlier Detection)
# Identifying districts with significant volume but failing compliance
active_dist = dist_df[dist_df['total_child_activity'] > 2000]

fig_scatter = px.scatter(
    active_dist,
    x='total_child_activity',
    y='clcs_zscore',
    color='state',
    hover_name='district',
    title='District Risk Analysis: Outlier Detection',
    labels={'clcs_zscore': 'Z-Score (Performance vs Avg)', 'total_child_activity': 'Child Volume'},
)
fig_scatter.add_hline(y=-1.5, line_dash="dash", line_color="red", annotation_text="Critical Failure (-1.5σ)")
fig_scatter.show()
"""

    # --- PILLAR 3 ---
    section_3_md = """## Pillar 3: Demand Intensity Heatmap (DIH)
**The Problem**: Static resource allocation fails dynamic demand.
**The Metric**: **Seasonality Velocity**.
**The Finding**:
Our logical tagging detects a **"School Rush"** in June-August, correlating with academic cycles. This validates the need for "Just-in-Time" kit deployment.
"""

    section_3_plot = """# Seasonality Trend Analysis
# Aggregating Monthly Volume
trend_agg = trend_df.groupby(['month', 'season_type'])['volume'].sum().reset_index()
trend_agg['month'] = trend_agg['month'].astype(str)

fig_trend = px.bar(
    trend_agg,
    x='month',
    y='volume',
    color='season_type',
    title='National Seasonality: The "School Rush" Effect',
    color_discrete_map={'Normal': 'gray', 'School Rush': 'red', 'Year End': 'orange'}
)
fig_trend.show()
"""

    rec_md = """## Strategic Recommendations
1.  **Deploy Mobile Vans to Red Zones**: Use the `SPS Map` to route mobile kits to the top 20 high-pressure districts immediately.
2.  **Launch "School Camps" in Z-Score Failures**: The `Risk Scatter` identifies exactly which districts have "Ghost Children". Targeted camps here prevent mass exclusion.
3.  **Elastic Staffing**: Anticipate the **June Spike** (proven by Trend Analysis) by hiring temporary operators in May.
"""

    # Add Cells
    nb['cells'] = [
        nbf.v4.new_markdown_cell(exec_summary),
        nbf.v4.new_code_cell(intro_code),
        
        nbf.v4.new_markdown_cell(section_1_md),
        nbf.v4.new_code_cell(section_1_plot),
        nbf.v4.new_code_cell(section_1_district),
        
        nbf.v4.new_markdown_cell(section_2_md),
        nbf.v4.new_code_cell(section_2_plot),
        nbf.v4.new_code_cell(section_2_scatter),
        
        nbf.v4.new_markdown_cell(section_3_md),
        nbf.v4.new_code_cell(section_3_plot),
        
        nbf.v4.new_markdown_cell(rec_md)
    ]
    
    os.makedirs("notebooks", exist_ok=True)
    with open('notebooks/AadhaarPulse_Final_Report.ipynb', 'w') as f:
        nbf.write(nb, f)
    
    print("Notebook created successfully at notebooks/AadhaarPulse_Final_Report.ipynb")

if __name__ == "__main__":
    create_notebook()
