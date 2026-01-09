import pandas as pd
import os
import re
from data_loader import load_and_merge_data, clean_column_names

def clean_district_names(df):
    """
    Cleans and standardizes district names.
    - Removes rows with numeric or single-char districts.
    - Standardizes casing.
    - Fixes known bad spellings (basic heuristic).
    """
    if 'district' not in df.columns:
        return df
        
    # Drop NaNs
    df = df.dropna(subset=['district'])
    
    # Ensure string
    df['district'] = df['district'].astype(str)
    
    # 1. Remove Garbage (Numeric, "?", short junk)
    # Filter out if district is purely numeric or length < 2 or contains "?"
    mask_valid = (
        ~df['district'].str.match(r'^\d+$') & 
        (df['district'].str.len() > 1) & 
        (~df['district'].str.contains(r'\?', regex=True))
    )
    df = df[mask_valid].copy()
    
    # 2. Standardization
    df['district'] = df['district'].str.strip().str.title()
    
    # 3. Known Fixes (Expand this list based on inspection)
    replacements = {
        'Ahmed Nagar': 'Ahmednagar',
        'Ahmadnagar': 'Ahmednagar',
        'Angul': 'Anugul',
        'Bangalore Urban': 'Bengaluru Urban',
        'Bangalore Rural': 'Bengaluru Rural',
        'Kalaburagi': 'Gulbarga', # Older name often mixed
        # Add more as discovered
    }
    df['district'] = df['district'].replace(replacements)
    
    return df

def calculate_pillars(base_path):
    print("--- Loading Data for Phase 2 Analysis ---")
    
    # Load and Clean
    bio_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_biometric/*.csv"))
    bio_df = clean_district_names(bio_df)
    
    demo_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_demographic/*.csv"))
    demo_df = clean_district_names(demo_df)
    
    enrol_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_enrolment/*.csv"))
    enrol_df = clean_district_names(enrol_df)
    
    # Create valid district-state map (filtering out inconsistencies)
    # We take the most frequent state for each district to avoid duplicates
    dist_state_map = enrol_df.groupby(['district'])['state'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]).reset_index()

    # --- Pillar 1: Service Accessibility Index (SAI) ---
    print("Calculating SAI (Service Pressure)...")
    
    # Volumes
    bio_vol = bio_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum().sum(axis=1)
    demo_vol = demo_df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum().sum(axis=1)
    enrol_vol = enrol_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum().sum(axis=1)
    
    total_vol = bio_vol.add(demo_vol, fill_value=0).add(enrol_vol, fill_value=0)
    
    # Active Pincodes
    all_pins = pd.concat([
        bio_df[['district', 'state', 'pincode']],
        demo_df[['district', 'state', 'pincode']],
        enrol_df[['district', 'state', 'pincode']]
    ])
    active_pins = all_pins.groupby('district')['pincode'].nunique()
    
    # SPS Formula: Total Volume / Active Pincodes
    sps_score = total_vol / active_pins.replace(0, 1)
    
    # --- Pillar 2: Child Lifecycle Compliance Score (CLCS) - REFINED ---
    print("Calculating CLCS (Child Risk) with Fixed Formula...")
    
    # New Logic: Compare "Bio Updates (5-17)" to "Total Child Activity (Enrolments + Updates)"
    # This proxies "share of child attention". 
    # If a district has 1000 new kids but 0 updates for older kids, it's a risk.
    
    child_updates_5_17 = bio_df.groupby('district')['bio_age_5_17'].sum()
    child_enrols_0_5 = enrol_df.groupby('district')['age_0_5'].sum()
    child_enrols_5_17 = enrol_df.groupby('district')['age_5_17'].sum()
    
    total_child_activity = child_updates_5_17.add(child_enrols_0_5, fill_value=0).add(child_enrols_5_17, fill_value=0)
    
    # Compliance Share = Updates / Total Interaction
    # Low score = Updates are neglected relative to enrolments
    clcs_score = child_updates_5_17 / total_child_activity.replace(0, 1)
    
    # --- Pillar 3: Demand Intensity Heatmap (DIH) ---
    print("Calculating DIH (Trends)...")
    
    # Date parsing
    for df in [bio_df, demo_df, enrol_df]:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            
    def agg_monthly(df, cols, type_name):
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby(['district', 'month'])[cols].sum().sum(axis=1).reset_index(name='volume')
        monthly['type'] = type_name
        return monthly

    bio_m = agg_monthly(bio_df, ['bio_age_5_17', 'bio_age_17_'], 'Biometric')
    demo_m = agg_monthly(demo_df, ['demo_age_5_17', 'demo_age_17_'], 'Demographic')
    enrol_m = agg_monthly(enrol_df, ['age_0_5', 'age_5_17', 'age_18_greater'], 'Enrolment')
    
    all_activity = pd.concat([bio_m, demo_m, enrol_m])
    
    # Monthly Total per District
    district_monthly_total = all_activity.groupby(['district', 'month'])['volume'].sum().reset_index()
    
    # --- Data Export - District Level ---
    results = pd.DataFrame({
        'total_volume': total_vol,
        'active_pincodes': active_pins,
        'sps_score': sps_score,
        'child_updates_5_17': child_updates_5_17,
        'child_enrols_0_5': child_enrols_0_5,
        'total_child_activity': total_child_activity,
        'clcs_score': clcs_score
    }).reset_index()
    
    results = results.merge(dist_state_map, on='district', how='left')
    results = results.fillna(0)
    
    # --- Aggregation: State Level ---
    print("Aggregating to State Level...")
    state_results = results.groupby('state').agg({
        'total_volume': 'sum',
        'active_pincodes': 'sum',
        'child_updates_5_17': 'sum',
        'child_enrols_0_5': 'sum',
        'total_child_activity': 'sum'
    }).reset_index()
    
    # Recalculate Scores at State Level (Weighted Average effectively)
    state_results['sps_score'] = state_results['total_volume'] / state_results['active_pincodes'].replace(0, 1)
    state_results['clcs_score'] = state_results['child_updates_5_17'] / state_results['total_child_activity'].replace(0, 1)
    
    # Save Files
    results.to_csv(os.path.join(base_path, 'aadhaar_pulse_district.csv'), index=False)
    state_results.to_csv(os.path.join(base_path, 'aadhaar_pulse_state.csv'), index=False)
    district_monthly_total.to_csv(os.path.join(base_path, 'aadhaar_pulse_trends.csv'), index=False)
    
    print("Phase 2 Analysis Complete. Saved district, state, and trend data.")

if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    calculate_pillars(BASE_PATH)
