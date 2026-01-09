import pandas as pd
import os
from data_loader import load_and_merge_data, clean_column_names

def calculate_pillars(base_path):
    print("--- Loading Data for Analysis ---")
    # Load all 3 datasets
    bio_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_biometric/*.csv"))
    demo_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_demographic/*.csv"))
    enrol_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_enrolment/*.csv"))
    
    # 1. Aggregation by District
    # We need to ensure we don't lose state mapping. 
    # Create a district-state map from any of the DFs to re-merge later if needed.
    dist_state_map = enrol_df[['district', 'state']].drop_duplicates()
    
    # --- Pillar 1: Service Accessibility Index (SAI) ---
    print("Calculating SAI (Service Pressure)...")
    
    # Calculate Total Volume per District
    # Biometric Volume
    bio_vol = bio_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum().sum(axis=1)
    # Demographic Volume
    demo_vol = demo_df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum().sum(axis=1)
    # Enrolment Volume
    enrol_vol = enrol_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum().sum(axis=1)
    
    total_vol = bio_vol.add(demo_vol, fill_value=0).add(enrol_vol, fill_value=0)
    
    # Calculate Unique Pincodes per District (Service Reach)
    # Combine pincodes from all datasets to get the true "Active Network"
    all_pins = pd.concat([
        bio_df[['district', 'pincode']],
        demo_df[['district', 'pincode']],
        enrol_df[['district', 'pincode']]
    ])
    active_pins = all_pins.groupby('district')['pincode'].nunique()
    
    # SPS Formula: Total Volume / Active Pincodes
    # Using 1 as minimum pincode to avoid division by zero
    sps_score = total_vol / active_pins.replace(0, 1)
    
    # --- Pillar 2: Child Lifecycle Compliance Score (CLCS) ---
    print("Calculating CLCS (Child Risk)...")
    
    # Metric: Bio Updates (5-17) / New Enrolments (0-5)
    # Rationale: If you have 1000 kids born (enrolled), you expect ~1000 updates eventually. 
    # Low ratio = Updates lagging behind generation rate.
    
    child_updates = bio_df.groupby('district')['bio_age_5_17'].sum()
    child_enrols = enrol_df.groupby('district')['age_0_5'].sum()
    
    # Avoid zero division
    crs_score = child_updates / child_enrols.replace(0, 1)
    
    # --- Pillar 3: Demand Intensity Heatmap (DIH) ---
    print("Calculating DIH (Peak Velocity)...")
    
    # Parse dates first
    for df in [bio_df, demo_df, enrol_df]:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
    
    # Combine all activity into a single timeline DF
    # We want Volume per Month per District
    
    # Helper to aggregate monthly
    def agg_monthly(df, cols, type_name):
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby(['district', 'month'])[cols].sum().sum(axis=1).reset_index(name='volume')
        monthly['type'] = type_name
        return monthly

    bio_m = agg_monthly(bio_df, ['bio_age_5_17', 'bio_age_17_'], 'Biometric')
    demo_m = agg_monthly(demo_df, ['demo_age_5_17', 'demo_age_17_'], 'Demographic')
    enrol_m = agg_monthly(enrol_df, ['age_0_5', 'age_5_17', 'age_18_greater'], 'Enrolment')
    
    all_activity = pd.concat([bio_m, demo_m, enrol_m])
    
    # Calculate Peak Monthly Volume per District
    district_monthly_total = all_activity.groupby(['district', 'month'])['volume'].sum().reset_index()
    peak_velocity = district_monthly_total.groupby('district')['volume'].max()
    
    
    # --- Combine Results ---
    results = pd.DataFrame({
        'total_volume': total_vol,
        'active_pincodes': active_pins,
        'sps_score': sps_score,
        'child_updates_5_17': child_updates,
        'child_enrols_0_5': child_enrols,
        'compliance_ratio': crs_score,
        'peak_monthly_volume': peak_velocity
    }).reset_index()
    
    # Add State Name back
    results = results.merge(dist_state_map, on='district', how='left')
    
    # Fill NaNs
    results = results.fillna(0)
    
    print("Analysis Complete. Results Head:")
    print(results.head())
    
    # Save
    output_path = os.path.join(base_path, 'aadhaar_pulse_analysis.csv')
    results.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")
    
    # Also save the monthly trend data for the Heatmap
    trend_output_path = os.path.join(base_path, 'aadhaar_pulse_monthly_trends.csv')
    district_monthly_total.to_csv(trend_output_path, index=False)
    print(f"Trends saved to {trend_output_path}")

if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    calculate_pillars(BASE_PATH)
