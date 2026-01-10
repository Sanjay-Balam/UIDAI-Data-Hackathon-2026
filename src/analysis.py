"""
Aadhaar Pulse 2.0 - Analysis Engine
====================================
Calculates the three pillars: SAI, CLCS, and DIH
"""

import pandas as pd
import numpy as np
import os
from data_loader import load_and_merge_data, clean_column_names
from cleaning_utils import normalize_state_names, normalize_district_names


def calculate_pillars(base_path: str) -> dict:
    """
    Main analysis function that calculates all three pillars.
    
    Returns:
        Dictionary containing district results, state results, and trends
    """
    print("=" * 60)
    print("🚀 AADHAAR PULSE 2.0 - Analysis Pipeline")
    print("=" * 60)
    
    # --- STEP 0: LOAD DATA ---
    print("\n📂 Loading Data...")
    bio_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_biometric/*.csv"))
    demo_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_demographic/*.csv"))
    enrol_df = clean_column_names(load_and_merge_data(base_path, "api_data_aadhar_enrolment/*.csv"))
    
    print(f"   Raw counts - Bio: {len(bio_df):,}, Demo: {len(demo_df):,}, Enrol: {len(enrol_df):,}")
    
    # --- STEP 1: DEEP CLEANING (P0 Fix) ---
    print("\n🧹 Performing Deep Data Cleaning...")
    
    # FIX: Properly reassign the cleaned DataFrames (not just loop variable)
    bio_df = normalize_state_names(bio_df)
    bio_df = normalize_district_names(bio_df)
    
    demo_df = normalize_state_names(demo_df)
    demo_df = normalize_district_names(demo_df)
    
    enrol_df = normalize_state_names(enrol_df)
    enrol_df = normalize_district_names(enrol_df)
    
    print(f"   Clean counts - Bio: {len(bio_df):,}, Demo: {len(demo_df):,}, Enrol: {len(enrol_df):,}")
    print(f"   Unique States: {enrol_df['state'].nunique()}")
    print(f"   Unique Districts: {enrol_df['district'].nunique()}")
    
    # Re-map District to State (using Mode to fix 'Adilabad' double-state issue)
    dist_state_map = enrol_df.groupby('district')['state'].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
    ).reset_index()
    
    # --- PILLAR 1: Service Accessibility Index (SAI) ---
    print("\n📊 Calculating Pillar 1: SAI (Service Pressure)...")
    
    bio_vol = bio_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum().sum(axis=1)
    demo_vol = demo_df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum().sum(axis=1)
    enrol_vol = enrol_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum().sum(axis=1)
    
    total_vol = bio_vol.add(demo_vol, fill_value=0).add(enrol_vol, fill_value=0)
    
    # Active Pincodes
    all_pins = pd.concat([
        bio_df[['district', 'pincode']],
        demo_df[['district', 'pincode']],
        enrol_df[['district', 'pincode']]
    ])
    active_pins = all_pins.groupby('district')['pincode'].nunique()
    
    sps_score = total_vol / active_pins.replace(0, 1)
    
    # --- PILLAR 2: Child Lifecycle Compliance Score (CLCS) ---
    print("📊 Calculating Pillar 2: CLCS (Z-Score Benchmarking)...")
    
    child_updates = bio_df.groupby('district')['bio_age_5_17'].sum()
    c_enrol_0_5 = enrol_df.groupby('district')['age_0_5'].sum()
    c_enrol_5_17 = enrol_df.groupby('district')['age_5_17'].sum()
    
    total_child_activity = child_updates.add(c_enrol_0_5, fill_value=0).add(c_enrol_5_17, fill_value=0)
    
    # Compliance Share
    compliance_share = child_updates / total_child_activity.replace(0, 1)
    
    # Z-Score Calculation
    national_mean = compliance_share.mean()
    national_std = compliance_share.std()
    clcs_zscore = (compliance_share - national_mean) / national_std
    
    # --- PILLAR 3: Demand Intensity Heatmap (DIH) ---
    print("📊 Calculating Pillar 3: DIH (Seasonality Analysis)...")
    
    # Parse dates
    bio_df['date'] = pd.to_datetime(bio_df['date'], format='%d-%m-%Y', errors='coerce')
    demo_df['date'] = pd.to_datetime(demo_df['date'], format='%d-%m-%Y', errors='coerce')
    enrol_df['date'] = pd.to_datetime(enrol_df['date'], format='%d-%m-%Y', errors='coerce')

    def agg_monthly(df, cols):
        df = df.copy()
        df['month'] = df['date'].dt.to_period('M')
        return df.groupby(['district', 'month'])[cols].sum().sum(axis=1).reset_index(name='volume')

    bio_m = agg_monthly(bio_df, ['bio_age_5_17', 'bio_age_17_'])
    demo_m = agg_monthly(demo_df, ['demo_age_5_17', 'demo_age_17_'])
    enrol_m = agg_monthly(enrol_df, ['age_0_5', 'age_5_17', 'age_18_greater'])
    
    all_activity = pd.concat([bio_m, demo_m, enrol_m])
    district_monthly_total = all_activity.groupby(['district', 'month'])['volume'].sum().reset_index()
    
    # Seasonality Tags
    def tag_season(month_obj):
        m = month_obj.month
        if m in [6, 7, 8]: return 'School Rush'
        if m in [12]: return 'Year End'
        if m in [3, 4]: return 'Financial Year End'
        return 'Normal'
        
    district_monthly_total['season_type'] = district_monthly_total['month'].apply(tag_season)
    
    # --- COMPILE RESULTS ---
    print("\n📊 Compiling Results...")
    
    results = pd.DataFrame({
        'total_volume': total_vol,
        'active_pincodes': active_pins,
        'sps_score': sps_score,
        'child_updates_5_17': child_updates,
        'total_child_activity': total_child_activity,
        'compliance_share': compliance_share,
        'clcs_zscore': clcs_zscore
    }).reset_index()
    
    results = results.merge(dist_state_map, on='district', how='left')
    results = results[results['state'].notna()]
    results = results.fillna(0)
    
    # State Aggregation
    state_results = results.groupby('state').agg({
        'total_volume': 'sum',
        'active_pincodes': 'sum',
        'child_updates_5_17': 'sum',
        'total_child_activity': 'sum',
        'district': 'count'
    }).reset_index()
    state_results = state_results.rename(columns={'district': 'num_districts'})
    
    state_results['sps_score'] = state_results['total_volume'] / state_results['active_pincodes'].replace(0, 1)
    state_results['compliance_share'] = state_results['child_updates_5_17'] / state_results['total_child_activity'].replace(0, 1)
    
    # State Z-Score
    state_mean = state_results['compliance_share'].mean()
    state_std = state_results['compliance_share'].std()
    state_results['clcs_zscore'] = (state_results['compliance_share'] - state_mean) / state_std
    
    # --- SAVE RESULTS ---
    results.to_csv(os.path.join(base_path, 'aadhaar_pulse_district_clean.csv'), index=False)
    state_results.to_csv(os.path.join(base_path, 'aadhaar_pulse_state_clean.csv'), index=False)
    district_monthly_total.to_csv(os.path.join(base_path, 'aadhaar_pulse_trends_clean.csv'), index=False)
    
    # --- PRINT SUMMARY ---
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"   📁 District Results: {len(results):,} districts")
    print(f"   📁 State Results: {len(state_results):,} states/UTs")
    print(f"   📁 Monthly Trends: {len(district_monthly_total):,} data points")
    
    print(f"\n   📈 Top 5 High-Pressure Districts (SAI):")
    top_sps = results.nlargest(5, 'sps_score')[['district', 'state', 'sps_score']]
    for _, row in top_sps.iterrows():
        print(f"      - {row['district']} ({row['state']}): {row['sps_score']:,.0f}")
    
    print(f"\n   ⚠️ Top 5 At-Risk Districts (Low CLCS Z-Score):")
    risk_districts = results[results['total_child_activity'] > 1000].nsmallest(5, 'clcs_zscore')[['district', 'state', 'clcs_zscore']]
    for _, row in risk_districts.iterrows():
        print(f"      - {row['district']} ({row['state']}): {row['clcs_zscore']:.2f}σ")
    
    return {
        'district': results,
        'state': state_results,
        'trends': district_monthly_total
    }


if __name__ == "__main__":
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    calculate_pillars(BASE_PATH)
