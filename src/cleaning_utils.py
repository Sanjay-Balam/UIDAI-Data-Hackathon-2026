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
    Uses lowercase matching for case-insensitivity.
    """
    if 'district' not in df.columns:
        return df
    
    df = df.copy()  # Avoid SettingWithCopyWarning
    df = df.dropna(subset=['district'])
    
    # 1. Normalize to lowercase for matching
    df['district'] = df['district'].astype(str).str.strip().str.lower()
    
    # 2. Regex Cleaning (Remove extra spaces, dots)
    df['district'] = df['district'].replace(r'\s+', ' ', regex=True)
    df['district'] = df['district'].replace(r'\.', '', regex=True)
    
    # 3. District Mapping (ALL LOWERCASE keys -> Proper Case values)
    dist_map = {
        # Karnataka - Bengaluru
        'bangalore': 'Bengaluru Urban', 
        'bangalore urban': 'Bengaluru Urban',
        'bengaluru': 'Bengaluru Urban',
        'bengaluru urban': 'Bengaluru Urban',
        'bangalore rural': 'Bengaluru Rural',
        'bengaluru rural': 'Bengaluru Rural',
        'bengaluru south': 'Bengaluru Urban',
        
        # Karnataka - Others
        'belgaum': 'Belagavi', 'belagavi': 'Belagavi',
        'gulbarga': 'Kalaburagi', 'kalaburagi': 'Kalaburagi',
        'mysore': 'Mysuru', 'mysuru': 'Mysuru',
        'shimoga': 'Shivamogga', 'shivamogga': 'Shivamogga',
        'bijapur': 'Vijayapura', 'vijayapura': 'Vijayapura',
        
        # Maharashtra / Gujarat
        'ahmed nagar': 'Ahmednagar', 'ahmadnagar': 'Ahmednagar', 'ahmednagar': 'Ahmednagar',
        'ahilyanagar': 'Ahmednagar',
        'ahmadabad': 'Ahmedabad', 'ahmedabad': 'Ahmedabad',
        
        # West Bengal - Parganas
        'north 24 parganas': 'North 24 Parganas',
        'north twenty four parganas': 'North 24 Parganas',
        '24 paraganas north': 'North 24 Parganas',
        'south 24 parganas': 'South 24 Parganas',
        'south twenty four parganas': 'South 24 Parganas',
        '24 paraganas south': 'South 24 Parganas',
        'south 24 pargana': 'South 24 Parganas',
        
        # West Bengal - Bardhaman
        'barddhaman': 'Bardhaman', 'bardhaman': 'Bardhaman',
        'purba bardhaman': 'Purba Bardhaman', 
        'paschim bardhaman': 'Paschim Bardhaman',
        'purba medinipur': 'Purba Medinipur', 'paschim medinipur': 'Paschim Medinipur',
        
        # West Bengal - Others
        'hooghly': 'Hooghly', 'hugli': 'Hooghly',
        'coochbehar': 'Cooch Behar', 'cooch behar': 'Cooch Behar', 'koch bihar': 'Cooch Behar',
        'dinajpur uttar': 'Uttar Dinajpur', 'uttar dinajpur': 'Uttar Dinajpur',
        'dinajpur dakshin': 'Dakshin Dinajpur', 'dakshin dinajpur': 'Dakshin Dinajpur',
        
        # Odisha
        'angul': 'Angul', 'anugul': 'Angul',
        'balasore': 'Balasore', 'baleshwar': 'Balasore',
        
        # Telangana
        'rangareddi': 'Rangareddy', 'kv rangareddy': 'Rangareddy', 'k v rangareddy': 'Rangareddy',
        'ranga reddy': 'Rangareddy', 'rangareddy': 'Rangareddy',
        'mahbubnagar': 'Mahabubnagar', 'mahaboobnagar': 'Mahabubnagar', 'mahabubnagar': 'Mahabubnagar',
        'medchal-malkajgiri': 'Medchal Malkajgiri', 'medchal?malkajgiri': 'Medchal Malkajgiri',
        
        # Tamil Nadu
        'kancheepuram': 'Kanchipuram', 'kanchipuram': 'Kanchipuram',
        'thiruvallur': 'Tiruvallur', 'tiruvallur': 'Tiruvallur',
        'tuticorin': 'Thoothukudi', 'thoothukkudi': 'Thoothukudi', 'thoothukudi': 'Thoothukudi',
        'tiruchirapalli': 'Tiruchirappalli', 'tiruchirappalli': 'Tiruchirappalli', 'trichy': 'Tiruchirappalli',
        
        # Andhra Pradesh
        'spsr nellore': 'Nellore', 'nellore': 'Nellore',
        'anantapur': 'Anantapur', 'ananthapuramu': 'Anantapur', 'ananthapur': 'Anantapur',
        
        # Bihar
        'purbi champaran': 'East Champaran', 'east champaran': 'East Champaran',
        'pashchimi champaran': 'West Champaran', 'west champaran': 'West Champaran',
        
        # Haryana
        'gurugram': 'Gurugram', 'gurgaon': 'Gurugram',
        'nuh': 'Nuh', 'mewat': 'Nuh',
        
        # UP
        'siddharth nagar': 'Siddharthnagar', 'siddharthnagar': 'Siddharthnagar',
        'allahabad': 'Prayagraj', 'prayagraj': 'Prayagraj',
        
        # MP
        'ashoknagar': 'Ashoknagar', 'ashok nagar': 'Ashoknagar',
    }
    
    # Apply mapping (keep original if not in map, but convert to title case)
    def map_district(name):
        if name in dist_map:
            return dist_map[name]
        # If not in map, convert to title case
        return name.title()
    
    df['district'] = df['district'].apply(map_district)
    
    # 4. Garbage Removal - Filter out invalid districts
    garbage_districts = {'100000', '5Th Cross', '5th Cross', '?', 'System', 'State', 'District', 'Akhera'}
    
    mask_valid = (
        df['district'].str.contains(r'[a-zA-Z]', na=False) & 
        (df['district'].str.len() > 2) & 
        (~df['district'].str.match(r'^\d+$', na=False)) &
        (~df['district'].isin(garbage_districts))
    )
    df = df[mask_valid]
    
    return df
