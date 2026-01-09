import pandas as pd
import os
import glob

def load_and_merge_data(base_path, pattern):
    """
    Loads multiple CSV files matching a pattern and merges them into a single DataFrame.
    """
    full_path = os.path.join(base_path, pattern)
    files = glob.glob(full_path)
    
    if not files:
        print(f"No files found for pattern: {full_path}")
        return pd.DataFrame()
    
    print(f"Found {len(files)} files for pattern '{pattern}'. Loading...")
    
    dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"Successfully merged {len(dfs)} files. Final shape: {merged_df.shape}")
    return merged_df

def clean_column_names(df):
    """Standardizes column names to lowercase and stripped."""
    df.columns = df.columns.str.strip().str.lower()
    return df

if __name__ == "__main__":
    # Correct base path for the user's workspace
    BASE_PATH = "/Users/balamsanjay/Desktop/UDIAI-DataHackthon/"
    
    # 1. Biometric Data (Updates)
    print("\n--- Process 1: Biometric Data ---")
    bio_df = load_and_merge_data(BASE_PATH, "api_data_aadhar_biometric/*.csv")
    if not bio_df.empty:
        bio_df = clean_column_names(bio_df)
        print("Columns:", bio_df.columns.tolist())
        # Convert date
        if 'date' in bio_df.columns:
            bio_df['date'] = pd.to_datetime(bio_df['date'], format='%d-%m-%Y', errors='coerce')

    # 2. Demographic Data (Updates)
    print("\n--- Process 2: Demographic Data ---")
    demo_df = load_and_merge_data(BASE_PATH, "api_data_aadhar_demographic/*.csv")
    if not demo_df.empty:
        demo_df = clean_column_names(demo_df)
        print("Columns:", demo_df.columns.tolist())
        if 'date' in demo_df.columns:
            demo_df['date'] = pd.to_datetime(demo_df['date'], format='%d-%m-%Y', errors='coerce')

    # 3. Enrolment Data (New Enrolments)
    print("\n--- Process 3: Enrolment Data ---")
    enrol_df = load_and_merge_data(BASE_PATH, "api_data_aadhar_enrolment/*.csv")
    if not enrol_df.empty:
        enrol_df = clean_column_names(enrol_df)
        print("Columns:", enrol_df.columns.tolist())
        if 'date' in enrol_df.columns:
            enrol_df['date'] = pd.to_datetime(enrol_df['date'], format='%d-%m-%Y', errors='coerce')
            
    # Save combined samples or just validation stats for now
    print("\n--- Data Validity Check ---")
    if not bio_df.empty:
        print(f"Biometric Date Range: {bio_df['date'].min()} to {bio_df['date'].max()}")
    if not enrol_df.empty:
        print(f"Enrolment Date Range: {enrol_df['date'].min()} to {enrol_df['date'].max()}")
