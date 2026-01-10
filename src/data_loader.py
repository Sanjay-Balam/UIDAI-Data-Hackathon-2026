"""
Data Loading Module for UIDAI Hackathon - Aadhaar Pulse 2.0
===========================================================
Handles loading and merging of multiple CSV files for each dataset.
"""

import pandas as pd
import os
import glob


def load_and_merge_data(base_path: str, pattern: str) -> pd.DataFrame:
    """
    Loads multiple CSV files matching a pattern and merges them into a single DataFrame.
    
    Args:
        base_path: Base directory containing the data folders
        pattern: Glob pattern to match files (e.g., "api_data_aadhar_biometric/*.csv")
    
    Returns:
        Merged DataFrame containing all data from matching files
    """
    full_path = os.path.join(base_path, pattern)
    files = sorted(glob.glob(full_path))
    
    if not files:
        print(f"⚠️ No files found for pattern: {full_path}")
        return pd.DataFrame()
    
    print(f"Found {len(files)} files for pattern '{pattern}'. Loading...")
    
    dfs = []
    total_rows = 0
    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            total_rows += len(df)
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"Successfully merged {len(dfs)} files. Final shape: {merged_df.shape}")
    return merged_df


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names to lowercase and stripped of whitespace.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with cleaned column names
    """
    if df.empty:
        return df
    df.columns = df.columns.str.strip().str.lower()
    return df


def load_all_datasets(base_path: str) -> dict:
    """
    Convenience function to load all three Aadhaar datasets.
    
    Args:
        base_path: Base directory containing the data folders
        
    Returns:
        Dictionary with keys 'enrolment', 'demographic', 'biometric'
    """
    print("=" * 60)
    print("📂 Loading All Aadhaar Datasets")
    print("=" * 60)
    
    datasets = {}
    
    # Enrolment Data
    print("\n1️⃣ Enrolment Data...")
    datasets['enrolment'] = clean_column_names(
        load_and_merge_data(base_path, "api_data_aadhar_enrolment/*.csv")
    )
    
    # Demographic Update Data
    print("\n2️⃣ Demographic Update Data...")
    datasets['demographic'] = clean_column_names(
        load_and_merge_data(base_path, "api_data_aadhar_demographic/*.csv")
    )
    
    # Biometric Update Data
    print("\n3️⃣ Biometric Update Data...")
    datasets['biometric'] = clean_column_names(
        load_and_merge_data(base_path, "api_data_aadhar_biometric/*.csv")
    )
    
    print("\n" + "=" * 60)
    print("✅ All datasets loaded successfully!")
    print("=" * 60)
    
    return datasets


if __name__ == "__main__":
    # Test the loader
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    
    # Load all datasets
    data = load_all_datasets(BASE_PATH)
    
    # Print summary
    print("\n📊 Dataset Summary:")
    for name, df in data.items():
        if not df.empty:
            print(f"\n{name.upper()}:")
            print(f"   Rows: {len(df):,}")
            print(f"   Columns: {df.columns.tolist()}")
            if 'date' in df.columns:
                print(f"   Date Range: {df['date'].min()} to {df['date'].max()}")
            if 'state' in df.columns:
                print(f"   Unique States: {df['state'].nunique()}")

