import pandas as pd
import numpy as np

def load_and_preprocess_data(filepath):
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            return None, "Unsupported file format"
        
        df.columns = df.columns.str.lower().str.strip()
        column_mapping = {
            'date': 'timestamp', 'datetime': 'timestamp', 'time': 'timestamp',
            'blood type': 'blood_type', 'unit': 'units', 'dept': 'department'
        }
        df = df.rename(columns=column_mapping)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        # Standardize strings
        df['blood_type'] = df['blood_type'].fillna('Unknown').astype(str).str.upper()
        df['department'] = df['department'].fillna('General')
        df['units'] = pd.to_numeric(df['units'], errors='coerce').fillna(0)
        
        return df, None
    except Exception as e:
        return None, str(e)

def get_clean_series(df, dept, bt):
    """Creates a continuous daily time series for a specific group"""
    subset = df[(df['department'] == dept) & (df['blood_type'] == bt)].copy()
    if subset.empty: return None
    
    # Aggregate to daily
    subset['date'] = subset['timestamp'].dt.date
    daily = subset.groupby('date')['units'].sum().reset_index()
    daily['date'] = pd.to_datetime(daily['date'])
    
    # Reindex to fill missing dates with 0 (Crucial for Statsmodels)
    daily = daily.set_index('date').resample('D').asfreq().fillna(0)
    return daily['units']
