"""
Export Static PNG Images for PDF Submission
============================================
Generates high-resolution PNG images for all visualizations.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import urllib.request

def export_all_images(base_path: str):
    """Export all visualizations as PNG images."""
    
    print("=" * 60)
    print("🖼️ Exporting Static Images for PDF Submission")
    print("=" * 60)
    
    # Load data
    district_df = pd.read_csv(os.path.join(base_path, 'aadhaar_pulse_district_clean.csv'))
    state_df = pd.read_csv(os.path.join(base_path, 'aadhaar_pulse_state_clean.csv'))
    trends_df = pd.read_csv(os.path.join(base_path, 'aadhaar_pulse_trends_clean.csv'))
    
    # Create output directory
    img_dir = os.path.join(base_path, 'images')
    os.makedirs(img_dir, exist_ok=True)
    
    # --- 1. SAI Bar Chart ---
    print("\n1️⃣ Exporting SAI Bar Chart...")
    top_pressure = district_df.nlargest(20, 'sps_score')
    
    fig_sps = px.bar(
        top_pressure,
        x='district',
        y='sps_score',
        color='state',
        title='<b>Top 20 Districts by Service Pressure Score (SAI)</b>',
        labels={'sps_score': 'Service Pressure Score', 'district': 'District'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_sps.update_layout(xaxis_tickangle=-45, height=500, width=1000)
    fig_sps.write_image(os.path.join(img_dir, '01_sai_top20.png'), scale=2)
    print("   ✅ Saved: 01_sai_top20.png")
    
    # --- 2. CLCS Risk Scatter ---
    print("\n2️⃣ Exporting CLCS Risk Scatter...")
    active_districts = district_df[district_df['total_child_activity'] > 1000]
    
    fig_risk = px.scatter(
        active_districts,
        x='total_child_activity',
        y='clcs_zscore',
        color='state',
        size='total_volume',
        hover_name='district',
        title='<b>Child Compliance Risk Map</b>',
        labels={'clcs_zscore': 'Compliance Z-Score (σ)', 'total_child_activity': 'Total Child Activity'},
        template='plotly_white',
        height=600, width=1000
    )
    fig_risk.add_hline(y=-1.5, line_dash="dash", line_color="red", annotation_text="HIGH RISK (-1.5σ)")
    fig_risk.add_hline(y=0, line_dash="dot", line_color="gray")
    fig_risk.write_image(os.path.join(img_dir, '02_clcs_risk_scatter.png'), scale=2)
    print("   ✅ Saved: 02_clcs_risk_scatter.png")
    
    # --- 3. India Map ---
    print("\n3️⃣ Exporting India Choropleth Map...")
    geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    
    try:
        with urllib.request.urlopen(geojson_url) as url:
            india_states = json.loads(url.read().decode())
        
        fig_map = px.choropleth(
            state_df,
            geojson=india_states,
            featureidkey='properties.ST_NM',
            locations='state',
            color='clcs_zscore',
            color_continuous_scale='RdYlGn',
            range_color=[-2, 2],
            title='<b>India: Child Compliance Z-Score by State</b>',
            template='plotly_white'
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=700, width=900)
        fig_map.write_image(os.path.join(img_dir, '03_india_map_clcs.png'), scale=2)
        print("   ✅ Saved: 03_india_map_clcs.png")
    except Exception as e:
        print(f"   ❌ Map export failed: {e}")
    
    # --- 4. Seasonality Trend ---
    print("\n4️⃣ Exporting Seasonality Trend...")
    national_trend = trends_df.groupby(['month', 'season_type'])['volume'].sum().reset_index()
    national_trend['month'] = national_trend['month'].astype(str)
    
    fig_trend = px.bar(
        national_trend,
        x='month',
        y='volume',
        color='season_type',
        title='<b>National Activity Volume by Month (Seasonality)</b>',
        labels={'volume': 'Total Transactions', 'month': 'Month'},
        template='plotly_white',
        color_discrete_map={
            'Normal': '#636EFA',
            'School Rush': '#EF553B',
            'Year End': '#FFA15A',
            'Financial Year End': '#00CC96'
        },
        height=450, width=1000
    )
    fig_trend.write_image(os.path.join(img_dir, '04_seasonality_trend.png'), scale=2)
    print("   ✅ Saved: 04_seasonality_trend.png")
    
    # --- 5. Demand Heatmap ---
    print("\n5️⃣ Exporting Demand Heatmap...")
    top_districts = district_df.nlargest(15, 'total_volume')['district'].tolist()
    heatmap_data = trends_df[trends_df['district'].isin(top_districts)]
    heatmap_pivot = heatmap_data.pivot_table(index='district', columns='month', values='volume', aggfunc='sum')
    
    fig_heatmap = px.imshow(
        heatmap_pivot,
        labels=dict(x="Month", y="District", color="Volume"),
        title='<b>Demand Intensity Heatmap (Top 15 Districts)</b>',
        template='plotly_white',
        aspect='auto',
        color_continuous_scale='YlOrRd'
    )
    fig_heatmap.update_layout(height=500, width=1000)
    fig_heatmap.write_image(os.path.join(img_dir, '05_demand_heatmap.png'), scale=2)
    print("   ✅ Saved: 05_demand_heatmap.png")
    
    # --- 6. Trivariate Analysis ---
    print("\n6️⃣ Exporting Trivariate Analysis...")
    fig_tri = px.scatter(
        state_df,
        x='sps_score',
        y='clcs_zscore',
        size='total_volume',
        color='num_districts',
        hover_name='state',
        title='<b>Trivariate: Service Pressure vs Child Compliance by State</b>',
        labels={'sps_score': 'Service Pressure Score', 'clcs_zscore': 'Child Compliance Z-Score'},
        template='plotly_white',
        height=550, width=900
    )
    fig_tri.add_vline(x=state_df['sps_score'].median(), line_dash="dash", line_color="gray")
    fig_tri.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_tri.write_image(os.path.join(img_dir, '06_trivariate_analysis.png'), scale=2)
    print("   ✅ Saved: 06_trivariate_analysis.png")
    
    # --- Summary ---
    print("\n" + "=" * 60)
    print("✅ ALL IMAGES EXPORTED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\n📁 Images saved to: {img_dir}")
    print("\nFiles created:")
    for f in sorted(os.listdir(img_dir)):
        if f.endswith('.png'):
            print(f"   - {f}")


if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    export_all_images(BASE_PATH)

