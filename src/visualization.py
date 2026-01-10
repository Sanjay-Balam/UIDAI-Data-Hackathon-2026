import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import urllib.request

def generate_visualizations(base_path):
    print("--- Generating Phase 3 Visualizations (Cleaned & Z-Scored) ---")
    
    # Load CLEAN Data
    district_path = os.path.join(base_path, 'aadhaar_pulse_district_clean.csv')
    state_path = os.path.join(base_path, 'aadhaar_pulse_state_clean.csv')
    trends_path = os.path.join(base_path, 'aadhaar_pulse_trends_clean.csv')
    
    if not os.path.exists(district_path):
        print("Clean Analysis files not found. Run analysis.py first.")
        return

    dist_df = pd.read_csv(district_path)
    state_df = pd.read_csv(state_path)
    trend_df = pd.read_csv(trends_path)
    
    output_dir = os.path.join(base_path, 'visualizations')
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 1. India Map (State Level) with Complete Boundaries (incl. J&K, Ladakh) ---
    print("Generating Clean Maps with Complete India Boundaries...")
    
    # GeoJSON includes J&K and Ladakh
    geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    india_states = None
    
    try:
        with urllib.request.urlopen(geojson_url) as url:
            india_states = json.loads(url.read().decode())
        print("   Loaded complete India GeoJSON (with J&K, Ladakh)")
    except Exception as e:
        print(f"   GeoJSON Error: {e}")

    if india_states:
        # Calculate State Z-Score dynamically for the map
        state_mean = state_df['compliance_share'].mean()
        state_std = state_df['compliance_share'].std()
        state_df['z_score'] = (state_df['compliance_share'] - state_mean) / state_std
        
        # Map state names to GeoJSON ST_NM property names
        state_name_map = {
            'Andaman & Nicobar Islands': 'Andaman & Nicobar',
            'Dadra & Nagar Haveli': 'Dadra and Nagar Haveli and Daman and Diu',
            'Daman & Diu': 'Dadra and Nagar Haveli and Daman and Diu',
        }
        state_df['state_geo'] = state_df['state'].map(lambda x: state_name_map.get(x, x))
        
        fig_map_clcs = px.choropleth(
            state_df,
            geojson=india_states,
            featureidkey='properties.ST_NM',
            locations='state_geo',
            color='z_score',
            color_continuous_scale='RdYlGn', 
            range_color=[-2, 2],
            title='State Compliance Z-Score (Deviation from National Avg)',
            template='plotly_dark',
            hover_name='state'
        )
        
        # Use lat/lon bounds to ensure J&K and Ladakh are visible
        fig_map_clcs.update_geos(
            visible=False,
            fitbounds="locations",
            projection_type="natural earth"
        )
        fig_map_clcs.update_layout(
            height=800, 
            margin=dict(l=0, r=0, t=50, b=0),
            geo=dict(
                lonaxis_range=[68, 98],  # Longitude range for India
                lataxis_range=[6, 38],   # Latitude range including J&K and Ladakh
            )
        )
        fig_map_clcs.write_html(os.path.join(output_dir, 'map_state_clcs_zscore.html'))

    # --- 2. Seasonality Trend ---
    print("Generating Trends with Seasonality...")
    # Aggregate National
    national_trend = trend_df.groupby(['month', 'season_type'])['volume'].sum().reset_index()
    national_trend['month'] = national_trend['month'].astype(str)
    
    fig_trend = px.bar(
        national_trend,
        x='month',
        y='volume',
        color='season_type', # Highlights School Rush vs Normal
        title='National Activity Volume & Seasonality (School Rush Detection)',
        template='plotly_dark',
        color_discrete_map={'Normal': 'gray', 'School Rush': 'red', 'Year End': 'orange'}
    )
    fig_trend.write_html(os.path.join(output_dir, 'trend_seasonality.html'))
    
    # --- 3. District Risk Scatter (Z-Score) ---
    print("Generating Risk Scatter...")
    
    # Filter for active districts
    active_dist = dist_df[dist_df['total_child_activity'] > 1000]
    
    fig_scatter = px.scatter(
        active_dist,
        x='total_child_activity',
        y='clcs_zscore',
        color='state',
        hover_name='district',
        title='District Risk Analysis: Z-Score vs Volume',
        labels={'clcs_zscore': 'Compliance Z-Score (Std Dev)', 'total_child_activity': 'Child Activity Volume'},
        template='plotly_dark'
    )
    # Add Risk Threshold line at -1.5 STD
    fig_scatter.add_hline(y=-1.5, line_dash="dash", line_color="red", annotation_text="High Risk Zone (-1.5σ)")
    fig_scatter.write_html(os.path.join(output_dir, 'chart_risk_zscore.html'))

    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    generate_visualizations(BASE_PATH)
