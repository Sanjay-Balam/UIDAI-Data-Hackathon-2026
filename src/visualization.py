import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import urllib.request

def generate_visualizations(base_path):
    print("--- Generating Phase 2 Visualizations ---")
    
    # Load Phase 2 Data
    district_path = os.path.join(base_path, 'aadhaar_pulse_district.csv')
    state_path = os.path.join(base_path, 'aadhaar_pulse_state.csv')
    trends_path = os.path.join(base_path, 'aadhaar_pulse_trends.csv')
    
    if not os.path.exists(district_path):
        print("Analysis files not found. Run analysis.py first.")
        return

    dist_df = pd.read_csv(district_path)
    state_df = pd.read_csv(state_path)
    trend_df = pd.read_csv(trends_path)
    
    output_dir = os.path.join(base_path, 'visualizations')
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 1. India Map (State Level Choropleth) ---
    print("Generating India Maps...")
    # Using a public GeoJSON for India States
    geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    try:
        with urllib.request.urlopen(geojson_url) as url:
            india_states = json.loads(url.read().decode())
    except:
        print("Could not download GeoJSON. Skipping Maps.")
        india_states = None

    if india_states:
        # Map 1: Service Pressure (SPS) by State
        fig_map_sps = px.choropleth(
            state_df,
            geojson=india_states,
            featureidkey='properties.ST_NM',
            locations='state',
            color='sps_score',
            color_continuous_scale='Reds',
            title='State-wise Service Pressure Score (SPS)',
            template='plotly_dark'
        )
        fig_map_sps.update_geos(fitbounds="locations", visible=False)
        fig_map_sps.write_html(os.path.join(output_dir, 'map_state_sps.html'))
        
        # Map 2: Child Compliance (CLCS) by State
        # Invert color because High Compliance is Good (Green), Low is Bad (Red)
        fig_map_clcs = px.choropleth(
            state_df,
            geojson=india_states,
            featureidkey='properties.ST_NM',
            locations='state',
            color='clcs_score',
            color_continuous_scale='RdYlGn', # Red to Green
            title='State-wise Child Compliance Score (CLCS)',
            template='plotly_dark'
        )
        fig_map_clcs.update_geos(fitbounds="locations", visible=False)
        fig_map_clcs.write_html(os.path.join(output_dir, 'map_state_clcs.html'))

    # --- 2. Trend Lines (Growth Velocity) ---
    print("Generating Trend Charts...")
    # Aggregate to National Level for a simple trend line
    national_trend = trend_df.groupby('month')['volume'].sum().reset_index()
    national_trend['month'] = national_trend['month'].astype(str)
    
    fig_trend = px.line(
        national_trend,
        x='month',
        y='volume',
        markers=True,
        title='National Aadhaar Activity Trend (Growth Velocity)',
        labels={'volume': 'Total Transactions', 'month': 'Month'},
        template='plotly_dark'
    )
    fig_trend.write_html(os.path.join(output_dir, 'trend_national_velocity.html'))
    
    # --- 3. District Leve Deep Dives (Improved) ---
    print("Generating District Charts...")
    
    # Top 20 Pressure Districts (Bar)
    top_pressure = dist_df.sort_values('sps_score', ascending=False).head(20)
    fig_bar = px.bar(
        top_pressure, x='district', y='sps_score', color='state',
        title='Top 20 Districts: Critical Service Pressure',
        template='plotly_dark'
    )
    fig_bar.write_html(os.path.join(output_dir, 'chart_district_sps_top20.html'))
    
    # Risk Scatter (CLCS vs Volume)
    # Filter valid data
    scatter_data = dist_df[(dist_df['total_child_activity'] > 500) & (dist_df['clcs_score'] < 1)]
    fig_scatter = px.scatter(
        scatter_data,
        x='total_child_activity',
        y='clcs_score',
        size='child_enrols_0_5', # Bubble size = New Enrolments (Risk Scale)
        color='state',
        hover_name='district',
        title='District Child Risk Map (Low Compliance vs High Activity)',
        labels={'clcs_score': 'Compliance Share', 'total_child_activity': 'Total Child Volume'},
        template='plotly_dark'
    )
    fig_scatter.add_hline(y=0.3, line_dash="dash", annotation_text="Critical Risk Threshold")
    fig_scatter.write_html(os.path.join(output_dir, 'chart_district_risk_scatter.html'))

    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    generate_visualizations(BASE_PATH)
