from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import logging
import re
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Vercel
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import warnings
import tempfile
warnings.filterwarnings('ignore')

# Configure matplotlib for serverless
plt.ioff()  # Turn off interactive mode

app = Flask(__name__)
CORS(app)

# Configure logging for serverless
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for serverless environment
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size for serverless

# Global variable to store current dataset (will use session storage in production)
current_data = None
current_filename = None
cleaning_operations = []

# Caching variables for data preview
preview_cache = None
preview_cache_hash = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_data_hash(data):
    """Generate a hash for the current state of data"""
    if data is None:
        return None
    try:
        # Use shape, column names, and first few values to create hash
        hash_components = [
            str(data.shape),
            str(sorted(data.columns.tolist())),
            str(data.head(3).to_string() if len(data) > 0 else "empty")
        ]
        return hash(''.join(hash_components))
    except Exception as e:
        logger.error(f"Error generating hash: {str(e)}")
        return None

def get_safe_sample_data(data, max_rows=1000):
    """Get a safe sample of data for preview"""
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    # If data is small enough, return it all
    if len(data) <= max_rows:
        return data.copy()
    
    # Otherwise, return a sample
    return data.sample(n=max_rows, random_state=42).copy()

def format_data_for_json(data):
    """Format DataFrame for JSON serialization with proper handling of all data types"""
    if data is None or len(data) == 0:
        return []
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = data.copy()
        
        # Handle different data types
        for col in df_copy.columns:
            if df_copy[col].dtype == 'datetime64[ns]':
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif df_copy[col].dtype == 'object':
                # Convert to string, handling NaN values
                df_copy[col] = df_copy[col].astype(str).replace('nan', '')
            elif pd.api.types.is_numeric_dtype(df_copy[col]):
                # Handle NaN in numeric columns
                df_copy[col] = df_copy[col].where(pd.notna(df_copy[col]), None)
        
        # Convert to records format
        return df_copy.to_dict('records')
    except Exception as e:
        logger.error(f"Error formatting data for JSON: {str(e)}")
        return []

def generate_plot_base64(plot_type, data, x_col, y_col=None, additional_params=None):
    """Generate a plot and return as base64 string"""
    try:
        plt.clf()  # Clear any existing plots
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if plot_type == 'histogram':
            if pd.api.types.is_numeric_dtype(data[x_col]):
                bins = additional_params.get('bins', 30) if additional_params else 30
                ax.hist(data[x_col].dropna(), bins=bins, alpha=0.7, edgecolor='black')
            else:
                value_counts = data[x_col].value_counts()
                ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
            ax.set_title(f'Histogram of {x_col}')
            ax.set_xlabel(x_col)
            ax.set_ylabel('Frequency')
        
        elif plot_type == 'scatter' and y_col:
            ax.scatter(data[x_col], data[y_col], alpha=0.6)
            ax.set_title(f'Scatter Plot: {x_col} vs {y_col}')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        
        elif plot_type == 'line' and y_col:
            ax.plot(data[x_col], data[y_col], marker='o', markersize=2)
            ax.set_title(f'Line Plot: {x_col} vs {y_col}')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        
        elif plot_type == 'box':
            if pd.api.types.is_numeric_dtype(data[x_col]):
                ax.boxplot(data[x_col].dropna())
                ax.set_title(f'Box Plot of {x_col}')
                ax.set_ylabel(x_col)
            else:
                # For categorical data, show distribution
                value_counts = data[x_col].value_counts()
                ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                ax.set_title(f'Distribution of {x_col}')
                ax.set_ylabel('Count')
        
        elif plot_type == 'bar':
            if y_col and pd.api.types.is_numeric_dtype(data[y_col]):
                grouped_data = data.groupby(x_col)[y_col].mean()
                ax.bar(range(len(grouped_data)), grouped_data.values)
                ax.set_xticks(range(len(grouped_data)))
                ax.set_xticklabels(grouped_data.index, rotation=45, ha='right')
                ax.set_title(f'Average {y_col} by {x_col}')
                ax.set_ylabel(f'Average {y_col}')
            else:
                value_counts = data[x_col].value_counts()
                ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                ax.set_title(f'Count by {x_col}')
                ax.set_ylabel('Count')
        
        plt.tight_layout()
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close(fig)  # Explicitly close the figure
        
        plot_base64 = base64.b64encode(plot_data).decode()
        return f"data:image/png;base64,{plot_base64}"
        
    except Exception as e:
        logger.error(f"Error generating plot: {str(e)}")
        plt.close('all')  # Close all figures in case of error
        return None