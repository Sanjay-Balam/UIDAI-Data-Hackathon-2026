import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

def generate_visualizations(base_path):
    print("--- Generating Visualizations ---")
    
    # Load analysis results
    analysis_path = os.path.join(base_path, 'aadhaar_pulse_analysis.csv')
    trends_path = os.path.join(base_path, 'aadhaar_pulse_monthly_trends.csv')
    
    if not os.path.exists(analysis_path):
        print("Analysis file not found.")
        return

    df = pd.read_csv(analysis_path)
    trends = pd.read_csv(trends_path)
    
    # Filter out junk districts (e.g. "?", "100000") if any, based on quick look at head
    df = df[~df['district'].isin(['?', '100000', '5th cross'])]
    
    output_dir = os.path.join(base_path, 'visualizations')
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Pillar 1: Service Pressure Score (SPS) ---
    print("Generating SAI Charts...")
    # Top 20 Districts with Highest Service Pressure
    top_pressure = df.sort_values('sps_score', ascending=False).head(20)
    
    fig_sps = px.bar(
        top_pressure, 
        x='district', 
        y='sps_score',
        color='total_volume',
        title='Top 20 Districts by Service Accessibility Pressure (SAI)',
        labels={'sps_score': 'Service Pressure Score (Txns / PIN)', 'district': 'District'},
        template='plotly_dark'
    )
    fig_sps.write_html(os.path.join(output_dir, 'sai_pressure_bar.html'))
    
    # --- Pillar 2: Child Lifecycle Compliance Score (CLCS) ---
    print("Generating CLCS Charts...")
    # Scatter Plot: Enrolment Volume vs Compliance Ratio
    # We want to find districts with High Enrolment (Right side) but Low Compliance (Bottom side) -> These are "Risk Zones"
    
    # Filter for meaningful volume to avoid noise
    significant_districts = df[df['child_enrols_0_5'] > 100] 
    
    fig_clcs = px.scatter(
        significant_districts,
        x='child_enrols_0_5',
        y='compliance_ratio',
        hover_name='district',
        color='state',
        title='Child Risk Map: Enrolment Volume vs Biometric Compliance',
        labels={'child_enrols_0_5': 'New Child Enrolments (0-5)', 'compliance_ratio': 'Compliance Ratio (Updates/Enrols)'},
        template='plotly_dark'
    )
    # Add lines to split quadrants?
    fig_clcs.add_hline(y=1.0, line_dash="dash", annotation_text="Ideal Compliance")
    fig_clcs.write_html(os.path.join(output_dir, 'clcs_risk_scatter.html'))
    
    # --- Pillar 3: Demand Intensity Heatmap (DIH) ---
    print("Generating DIH Charts...")
    # We need a matrix of District vs Month for Volume
    # Let's pick Top 20 Districts by Total Volume for the Heatmap to keep it readable
    top_vol_districts = df.sort_values('total_volume', ascending=False).head(20)['district'].tolist()
    
    heatmap_data = trends[trends['district'].isin(top_vol_districts)]
    
    # Pivot for heatmap
    heatmap_matrix = heatmap_data.pivot(index='district', columns='month', values='volume')
    heatmap_matrix = heatmap_matrix.fillna(0)
    
    fig_dih = px.imshow(
        heatmap_matrix,
        labels=dict(x="Month", y="District", color="Volume"),
        title="Demand Intensity Heatmap (Top 20 Districts)",
        template='plotly_dark',
        aspect="auto"
    )
    fig_dih.write_html(os.path.join(output_dir, 'dih_heatmap.html'))
    
    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    generate_visualizations(BASE_PATH)
