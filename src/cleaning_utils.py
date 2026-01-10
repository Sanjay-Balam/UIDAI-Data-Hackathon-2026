import pandas as pd
import re

# Valid Indian States/UTs (Official 36)
VALID_STATES = {
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman & Nicobar Islands', 'Chandigarh', 'Dadra & Nagar Haveli',
    'Daman & Diu', 'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
}

def normalize_state_names(df):
    """
    Standardizes state names to official 36 State/UT format.
    Fixes variations like 'West Bangal', 'Orissa', 'Pondicherry'.
    Also removes garbage rows with invalid state names.
    """
    if 'state' not in df.columns:
        return df
    
    df = df.copy()  # Avoid SettingWithCopyWarning
    
    # Standardize casing first (lowercase for matching, then apply proper case)
    df['state'] = df['state'].astype(str).str.strip().str.lower()
    
    # State Mapping Dictionary (all lowercase keys for matching)
    state_map = {
        # West Bengal variations
        'west bengal': 'West Bengal', 'westbengal': 'West Bengal', 'west bangal': 'West Bengal', 
        'w.bengal': 'West Bengal', 'wb': 'West Bengal', 'west  bengal': 'West Bengal',
        
        # Odisha
        'orissa': 'Odisha', 'odisha': 'Odisha',
        
        # J&K
        'jammu and kashmir': 'Jammu & Kashmir', 'jammu & kashmir': 'Jammu & Kashmir', 
        'j & k': 'Jammu & Kashmir', 'j&k': 'Jammu & Kashmir',
        
        # Puducherry
        'pondicherry': 'Puducherry', 'puducherry': 'Puducherry',
        
        # Andaman
        'andaman and nicobar islands': 'Andaman & Nicobar Islands',
        'andaman & nicobar islands': 'Andaman & Nicobar Islands',
        'andaman & nicobar': 'Andaman & Nicobar Islands',
        
        # Dadra & Nagar Haveli and Daman & Diu
        'dadra and nagar haveli': 'Dadra & Nagar Haveli',
        'dadra & nagar haveli': 'Dadra & Nagar Haveli',
        'dadra and nagar haveli and daman and diu': 'Dadra & Nagar Haveli',
        'the dadra and nagar haveli and daman and diu': 'Dadra & Nagar Haveli',
        'daman and diu': 'Daman & Diu',
        'daman & diu': 'Daman & Diu',
        
        # Delhi
        'delhi': 'Delhi', 'nct of delhi': 'Delhi', 'new delhi': 'Delhi',
        
        # Tamil Nadu
        'tamil nadu': 'Tamil Nadu', 'tamilnadu': 'Tamil Nadu',
        
        # All standard states (lowercase -> proper case)
        'andhra pradesh': 'Andhra Pradesh', 'arunachal pradesh': 'Arunachal Pradesh',
        'assam': 'Assam', 'bihar': 'Bihar', 'chhattisgarh': 'Chhattisgarh',
        'goa': 'Goa', 'gujarat': 'Gujarat', 'haryana': 'Haryana',
        'himachal pradesh': 'Himachal Pradesh', 'jharkhand': 'Jharkhand',
        'karnataka': 'Karnataka', 'kerala': 'Kerala', 'madhya pradesh': 'Madhya Pradesh',
        'maharashtra': 'Maharashtra', 'manipur': 'Manipur', 'meghalaya': 'Meghalaya',
        'mizoram': 'Mizoram', 'nagaland': 'Nagaland', 'punjab': 'Punjab',
        'rajasthan': 'Rajasthan', 'sikkim': 'Sikkim', 'telangana': 'Telangana',
        'tripura': 'Tripura', 'uttar pradesh': 'Uttar Pradesh', 'uttarakhand': 'Uttarakhand',
        'chandigarh': 'Chandigarh', 'ladakh': 'Ladakh', 'lakshadweep': 'Lakshadweep'
    }
    
    # Apply Mapping
    df['state'] = df['state'].map(lambda x: state_map.get(x, None))
    
    # Remove rows with invalid/unmapped states (garbage like '0', '100000', 'state')
    df = df.dropna(subset=['state'])
    
    return df

def normalize_district_names(df):
    """
    Standardizes district names to fix duplicates.
    Fixes 'Bengaluru' vs 'Bangalore', 'North 24 Parganas', etc.
    """
    if 'district' not in df.columns:
        return df
        
    df = df.dropna(subset=['district'])
    df['district'] = df['district'].astype(str).str.strip().str.title()
    
    # 1. Regex Cleaning (Remove extra spaces, dots)
    df['district'] = df['district'].replace(r'\s+', ' ', regex=True)
    df['district'] = df['district'].replace(r'\.', '', regex=True) # W.Godavari -> W Godavari
    
    # 2. Hard-coded Duplication Fixes
    dist_map = {
        # Bengaluru
        'Bangalore': 'Bengaluru Urban', 
        'Bangalore Urban': 'Bengaluru Urban',
        'Bengaluru': 'Bengaluru Urban',
        'Bangalore Rural': 'Bengaluru Rural',
        
        # Belagavi
        'Belgaum': 'Belagavi', 'Belagavi': 'Belagavi',
        
        # Kalaburagi
        'Gulbarga': 'Kalaburagi', 'Kalaburagi': 'Kalaburagi',
        
        # Mysuru
        'Mysore': 'Mysuru', 'Mysuru': 'Mysuru',
        
        # Shivamogga
        'Shimoga': 'Shivamogga', 'Shivamogga': 'Shivamogga',
        
        # Vijayapura
        'Bijapur': 'Vijayapura', 'Vijayapura': 'Vijayapura', # Note: Bijapur also exists in Chhattisgarh! Need State context ideally.
        # But usually in Aadhaar data, Karnataka volume dominates this name. We assume Karnataka for now.
        
        # Maharashtra
        'Ahmed Nagar': 'Ahmednagar', 'Ahmadnagar': 'Ahmednagar',
        'Ahmadabad': 'Ahmedabad', # Gujarat
        
        # West Bengal - The Parganas Nightmare
        'North 24 Parganas': 'North 24 Parganas',
        'North Twenty Four Parganas': 'North 24 Parganas',
        '24 Paraganas North': 'North 24 Parganas',
        'South 24 Parganas': 'South 24 Parganas',
        'South Twenty Four Parganas': 'South 24 Parganas',
        'Barddhaman': 'Bardhaman', 'Purba Bardhaman': 'Bardhaman', 'Paschim Bardhaman': 'Bardhaman', 
        # (Merging Bardhaman split for historical consistency if needed, or keep separate if new)
        
        # Odisha
        'Angul': 'Anugul', 'Anugul': 'Anugul',
        'Balasore': 'Baleshwar', 'Baleshwar': 'Baleshwar',
        
        # Telangana
        'Rangareddi': 'Rangareddy', 'K.V.Rangareddy': 'Rangareddy', 'Ranga Reddy': 'Rangareddy',
        'Mahbubnagar': 'Mahabubnagar', 'Mahaboobnagar': 'Mahabubnagar',
        
        # Tamil Nadu
        'Kancheepuram': 'Kanchipuram', 'Kanchipuram': 'Kanchipuram',
        'Thiruvallur': 'Tiruvallur', 'Tiruvallur': 'Tiruvallur',
        'Tuticorin': 'Thoothukkudi', 'Thoothukkudi': 'Thoothukkudi'
    }
    
    # Context-aware replacement is hard without state column in the map function.
    # For now, distinct names are mapped globally.
    df['district'] = df['district'].map(lambda x: dist_map.get(x, x))
    
    # 3. Garbage Removal
    # Filter out numeric districts, "?", "5th Cross"
    # Keep only if it has at least one letter and length > 2
    mask_valid = (
        df['district'].str.contains(r'[a-zA-Z]') & 
        (df['district'].str.len() > 2) & 
        (~df['district'].str.contains(r'^\d+$')) &
        (~df['district'].isin(['100000', '5th Cross', 'System']))
    )
    df = df[mask_valid]
    
    return df
