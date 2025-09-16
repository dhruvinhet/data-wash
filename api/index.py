from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import tempfile
from werkzeug.utils import secure_filename
import logging

# Try to import data libraries, fall back gracefully
try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
    np = None

try:
    import openpyxl
    HAS_EXCEL = True
except ImportError:
    HAS_EXCEL = False

app = Flask(__name__)
CORS(app, origins=["*"])

# Global storage (in production, use Redis or database)
data_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

def handler(request):
    """Main handler for all API routes"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    try:
        path = request.path
        method = request.method
        
        # Route handling
        if path == '/api/upload' and method == 'POST':
            return handle_upload(request), 200, headers
        elif path == '/api/preview' and method == 'GET':
            return handle_preview(request), 200, headers
        elif path == '/api/info' and method == 'GET':
            return handle_info(request), 200, headers
        elif path == '/api/data' and method == 'GET':
            return handle_data(request), 200, headers
        elif path == '/api/plot' and method == 'POST':
            return handle_plot(request), 200, headers
        elif path == '/api/correlation' and method == 'GET':
            return handle_correlation(request), 200, headers
        elif path == '/api/drop-columns' and method == 'POST':
            return handle_drop_columns(request), 200, headers
        elif path == '/api/impute-missing' and method == 'POST':
            return handle_impute_missing(request), 200, headers
        else:
            return jsonify({'error': 'Route not found'}), 404, headers
            
    except Exception as e:
        logging.error(f"Error in handler: {str(e)}")
        return jsonify({'error': str(e)}), 500, headers

def handle_upload(request):
    """Handle file upload"""
    try:
        if not HAS_PANDAS:
            return jsonify({'error': 'Data processing libraries not available'})
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}")
            file.save(temp_file.name)
            
            # Read the file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_file.name)
            else:
                if not HAS_EXCEL:
                    return jsonify({'error': 'Excel support not available'})
                df = pd.read_excel(temp_file.name)
            
            # Store in global storage (in production, use proper storage)
            session_id = 'default'  # In production, use proper session management
            data_store[session_id] = {
                'data': df,
                'filename': file.filename,
                'operations': []
            }
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': file.filename,
                'shape': df.shape,
                'columns': df.columns.tolist()
            })
        else:
            return jsonify({'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'error': str(e)})

def handle_preview(request):
    """Handle data preview"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    df = data_store[session_id]['data']
    
    # Get first 5 rows and last 5 rows
    preview_data = []
    total_rows = len(df)
    
    if total_rows <= 10:
        preview_data = df.to_dict('records')
    else:
        first_5 = df.head(5).to_dict('records')
        last_5 = df.tail(5).to_dict('records')
        preview_data = first_5 + [{'...': '... {} more rows ...'.format(total_rows - 10)}] + last_5
    
    return jsonify({
        'data': preview_data,
        'total_rows': total_rows,
        'columns': df.columns.tolist()
    })

def handle_info(request):
    """Handle dataset info"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    df = data_store[session_id]['data']
    
    # Calculate basic info
    info = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum() / (1024 * 1024),  # MB
    }
    
    # Add basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        info['statistics'] = df[numeric_cols].describe().to_dict()
    
    return jsonify(info)

def handle_data(request):
    """Handle full data request"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    df = data_store[session_id]['data']
    
    # Convert data for JSON serialization
    data_dict = df.to_dict('records')
    
    return jsonify({
        'data': data_dict,
        'shape': df.shape,
        'columns': df.columns.tolist()
    })

def handle_plot(request):
    """Handle plot generation"""
    # For now, return a simple response
    # In production, you'd generate actual plots
    return jsonify({
        'plot_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    })

def handle_correlation(request):
    """Handle correlation matrix"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    df = data_store[session_id]['data']
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return jsonify({'error': 'Not enough numeric columns for correlation'})
    
    correlation_matrix = df[numeric_cols].corr()
    
    return jsonify({
        'correlation_matrix': correlation_matrix.to_dict(),
        'columns': numeric_cols.tolist()
    })

def handle_drop_columns(request):
    """Handle column dropping"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    data = request.get_json()
    columns_to_drop = data.get('columns', [])
    
    df = data_store[session_id]['data']
    df_modified = df.drop(columns=columns_to_drop)
    
    # Update stored data
    data_store[session_id]['data'] = df_modified
    data_store[session_id]['operations'].append({
        'type': 'drop_columns',
        'columns': columns_to_drop,
        'timestamp': pd.Timestamp.now().isoformat()
    })
    
    return jsonify({
        'message': f'Successfully dropped {len(columns_to_drop)} columns',
        'new_shape': df_modified.shape,
        'remaining_columns': df_modified.columns.tolist()
    })

def handle_impute_missing(request):
    """Handle missing value imputation"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    data = request.get_json()
    method = data.get('method', 'mean')
    columns = data.get('columns', [])
    
    df = data_store[session_id]['data'].copy()
    
    for col in columns:
        if col in df.columns:
            if method == 'mean' and pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].mean(), inplace=True)
            elif method == 'median' and pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)
            elif method == 'mode':
                mode_value = df[col].mode()[0] if len(df[col].mode()) > 0 else 0
                df[col].fillna(mode_value, inplace=True)
            elif method == 'drop':
                df.dropna(subset=[col], inplace=True)
    
    # Update stored data
    data_store[session_id]['data'] = df
    data_store[session_id]['operations'].append({
        'type': 'impute_missing',
        'method': method,
        'columns': columns,
        'timestamp': pd.Timestamp.now().isoformat()
    })
    
    return jsonify({
        'message': f'Successfully imputed missing values using {method} method',
        'new_shape': df.shape,
        'missing_values': df.isnull().sum().to_dict()
    })

# For Vercel serverless deployment
def main(request):
    return handler(request)