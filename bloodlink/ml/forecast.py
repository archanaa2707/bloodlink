import pandas as pd
import numpy as np
from ml.preprocess import load_and_preprocess_data, extract_features
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt

def predict_blood_demand(filepath):
    """Predict blood demand levels and generate visualizations"""
    try:
        # Load and preprocess data
        df, error = load_and_preprocess_data(filepath)
        
        if error:
            return {'success': False, 'error': error}
        
        # Extract features
        features, error = extract_features(df)
        
        if error:
            return {'success': False, 'error': error}
        
        # Generate predictions
        predictions = generate_predictions(features)
        
        # Generate visualizations
        charts = generate_charts(df, predictions)
        
        return {
            'success': True,
            'predictions': predictions,
            'charts': charts,
            'summary': generate_summary(predictions)
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_predictions(features):
    """Generate demand predictions based on features"""
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    predictions = {}
    
    for bt in blood_types:
        avg_key = f'{bt}_avg'
        std_key = f'{bt}_std'
        trend_key = f'{bt}_trend'
        
        if avg_key in features:
            avg = features[avg_key]
            std = features[std_key]
            trend = features[trend_key]
            
            # Simple prediction: avg + trend * future_periods
            predicted_demand = avg + (trend * 7)  # 7 days ahead
            
            # Classify demand level
            if predicted_demand > avg + std:
                level = 'HIGH'
            elif predicted_demand < avg - std:
                level = 'LOW'
            else:
                level = 'NORMAL'
            
            predictions[bt] = {
                'predicted_units': max(0, round(predicted_demand, 2)),
                'level': level,
                'confidence': min(95, 70 + abs(trend) * 10)  # Simple confidence score
            }
        else:
            predictions[bt] = {
                'predicted_units': 0,
                'level': 'INSUFFICIENT_DATA',
                'confidence': 0
            }
    
    return predictions

def generate_charts(df, predictions):
    """Generate charts as base64 encoded images"""
    charts = {}
    
    try:
        # Chart 1: Blood type demand prediction
        fig, ax = plt.subplots(figsize=(10, 6))
        blood_types = list(predictions.keys())
        predicted_units = [predictions[bt]['predicted_units'] for bt in blood_types]
        colors = ['red' if predictions[bt]['level'] == 'HIGH' else 
                 'orange' if predictions[bt]['level'] == 'NORMAL' else 'green' 
                 for bt in blood_types]
        
        ax.bar(blood_types, predicted_units, color=colors)
        ax.set_xlabel('Blood Type')
        ax.set_ylabel('Predicted Units Needed')
        ax.set_title('7-Day Blood Demand Forecast by Type')
        ax.grid(axis='y', alpha=0.3)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        charts['demand_forecast'] = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        # Chart 2: Historical trend (if data available)
        if 'date' in df.columns and 'units_requested' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Group by date and sum units
            daily_demand = df.groupby('date')['units_requested'].sum()
            ax.plot(daily_demand.index, daily_demand.values, marker='o', linewidth=2)
            ax.set_xlabel('Date')
            ax.set_ylabel('Total Units Requested')
            ax.set_title('Historical Blood Demand Trend')
            ax.grid(alpha=0.3)
            plt.xticks(rotation=45)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            charts['historical_trend'] = base64.b64encode(buffer.read()).decode()
            plt.close()
    
    except Exception as e:
        print(f"Error generating charts: {e}")
    
    return charts

def generate_summary(predictions):
    """Generate text summary of predictions"""
    high_demand = [bt for bt, pred in predictions.items() if pred['level'] == 'HIGH']
    low_demand = [bt for bt, pred in predictions.items() if pred['level'] == 'LOW']
    
    summary = []
    
    if high_demand:
        summary.append(f"HIGH DEMAND ALERT: Blood types {', '.join(high_demand)} are expected to be in high demand.")
    
    if low_demand:
        summary.append(f"✓ Adequate supply predicted for: {', '.join(low_demand)}")
    
    total_predicted = sum(pred['predicted_units'] for pred in predictions.values())
    summary.append(f"📊 Total predicted demand for next 7 days: {round(total_predicted)} units")
    
    return ' '.join(summary) if summary else "Demand levels are normal across all blood types."
