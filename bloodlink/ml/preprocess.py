import pandas as pd
import numpy as np

def load_and_preprocess_data(filepath):
    """Load and preprocess the uploaded data file"""
    try:
        # Read file based on extension
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            return None, "Unsupported file format"
        
        # Expected columns (flexible)
        # The file should contain historical data with columns like:
        # date, blood_type, units_requested, units_donated, etc.
        
        # Basic preprocessing
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            df = df.sort_values('date')
        
        # Handle missing values
        df = df.fillna(0)
        
        return df, None
    
    except Exception as e:
        return None, str(e)

def extract_features(df):
    """Extract features for prediction"""
    try:
        features = {}
        
        # Calculate demand statistics by blood type
        if 'blood_type' in df.columns and 'units_requested' in df.columns:
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            
            for bt in blood_types:
                bt_data = df[df['blood_type'] == bt]
                if not bt_data.empty:
                    features[f'{bt}_avg'] = bt_data['units_requested'].mean()
                    features[f'{bt}_std'] = bt_data['units_requested'].std()
                    features[f'{bt}_trend'] = calculate_trend(bt_data)
                else:
                    features[f'{bt}_avg'] = 0
                    features[f'{bt}_std'] = 0
                    features[f'{bt}_trend'] = 0
        
        # Calculate overall statistics
        if 'units_requested' in df.columns:
            features['total_avg'] = df['units_requested'].mean()
            features['total_std'] = df['units_requested'].std()
            features['total_max'] = df['units_requested'].max()
        
        return features, None
    
    except Exception as e:
        return None, str(e)

def calculate_trend(data):
    """Calculate trend direction (simple linear trend)"""
    if len(data) < 2:
        return 0
    
    x = np.arange(len(data))
    y = data['units_requested'].values
    
    # Simple linear regression
    coeffs = np.polyfit(x, y, 1)
    return coeffs[0]  # Return slope