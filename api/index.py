from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import tempfile
from werkzeug.utils import secure_filename
import logging
import csv
import io
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["*"])

# Global storage (in production, use Redis or database)
data_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

def read_csv_file(filepath):
    """Read CSV file using built-in csv module"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            data.append(row)
    return data, columns

def get_basic_stats(data, columns):
    """Get basic statistics without pandas"""
    stats = {}
    total_rows = len(data)
    
    for col in columns:
        values = [row.get(col, '') for row in data]
        non_empty = [v for v in values if v and str(v).strip()]
        missing = total_rows - len(non_empty)
        
        # Try to convert to numbers
        numeric_values = []
        for v in non_empty:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue
        
        col_stats = {
            'missing': missing,
            'non_null': len(non_empty),
            'dtype': 'numeric' if len(numeric_values) > len(non_empty) * 0.5 else 'object'
        }
        
        if numeric_values:
            col_stats['mean'] = sum(numeric_values) / len(numeric_values)
            col_stats['min'] = min(numeric_values)
            col_stats['max'] = max(numeric_values)
        
        stats[col] = col_stats
    
    return stats

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
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            file.save(temp_file.name)
            
            # Read the CSV file
            data, columns = read_csv_file(temp_file.name)
            
            # Store in global storage
            session_id = 'default'
            data_store[session_id] = {
                'data': data,
                'columns': columns,
                'filename': file.filename,
                'operations': []
            }
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': file.filename,
                'shape': [len(data), len(columns)],
                'columns': columns
            })
        else:
            return jsonify({'error': 'Only CSV files are supported in this lightweight version'})
    except Exception as e:
        return jsonify({'error': str(e)})

def handle_preview(request):
    """Handle data preview"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    data = data_store[session_id]['data']
    
    # Get first 5 rows and last 5 rows
    preview_data = []
    total_rows = len(data)
    
    if total_rows <= 10:
        preview_data = data
    else:
        first_5 = data[:5]
        last_5 = data[-5:]
        preview_data = first_5 + [{'...': f'... {total_rows - 10} more rows ...'}] + last_5
    
    return jsonify({
        'data': preview_data,
        'total_rows': total_rows,
        'columns': data_store[session_id]['columns']
    })

def handle_info(request):
    """Handle dataset info"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    data = data_store[session_id]['data']
    columns = data_store[session_id]['columns']
    
    # Calculate basic info
    stats = get_basic_stats(data, columns)
    
    info = {
        'shape': [len(data), len(columns)],
        'columns': columns,
        'dtypes': {col: stats[col]['dtype'] for col in columns},
        'missing_values': {col: stats[col]['missing'] for col in columns},
        'memory_usage': len(str(data)) / (1024 * 1024),  # Rough estimate
    }
    
    # Add basic statistics for numeric columns
    statistics = {}
    for col in columns:
        if stats[col]['dtype'] == 'numeric' and 'mean' in stats[col]:
            statistics[col] = {
                'count': stats[col]['non_null'],
                'mean': stats[col]['mean'],
                'min': stats[col]['min'],
                'max': stats[col]['max']
            }
    
    if statistics:
        info['statistics'] = statistics
    
    return jsonify(info)

def handle_data(request):
    """Handle full data request"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    data = data_store[session_id]['data']
    columns = data_store[session_id]['columns']
    
    return jsonify({
        'data': data,
        'shape': [len(data), len(columns)],
        'columns': columns
    })

def handle_plot(request):
    """Handle plot generation"""
    # Return a simple placeholder for plotting
    return jsonify({
        'plot_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
        'message': 'Plotting functionality requires pandas and matplotlib (not available in lightweight version)'
    })

def handle_correlation(request):
    """Handle correlation matrix"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    return jsonify({
        'error': 'Correlation matrix requires pandas and numpy (not available in lightweight version)'
    })

def handle_drop_columns(request):
    """Handle column dropping"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    req_data = request.get_json()
    columns_to_drop = req_data.get('columns', [])
    
    data = data_store[session_id]['data']
    columns = data_store[session_id]['columns']
    
    # Remove columns from data
    new_data = []
    for row in data:
        new_row = {k: v for k, v in row.items() if k not in columns_to_drop}
        new_data.append(new_row)
    
    # Update columns list
    new_columns = [col for col in columns if col not in columns_to_drop]
    
    # Update stored data
    data_store[session_id]['data'] = new_data
    data_store[session_id]['columns'] = new_columns
    data_store[session_id]['operations'].append({
        'type': 'drop_columns',
        'columns': columns_to_drop,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'message': f'Successfully dropped {len(columns_to_drop)} columns',
        'new_shape': [len(new_data), len(new_columns)],
        'remaining_columns': new_columns
    })

def handle_impute_missing(request):
    """Handle missing value imputation"""
    session_id = 'default'
    if session_id not in data_store:
        return jsonify({'error': 'No data uploaded'})
    
    req_data = request.get_json()
    method = req_data.get('method', 'mean')
    columns_to_impute = req_data.get('columns', [])
    
    data = data_store[session_id]['data']
    
    # Simple imputation
    for col in columns_to_impute:
        values = [row.get(col, '') for row in data]
        non_empty = [v for v in values if v and str(v).strip()]
        
        if method == 'mode' and non_empty:
            # Most common value
            most_common = max(set(non_empty), key=non_empty.count)
            for row in data:
                if not row.get(col, '').strip():
                    row[col] = most_common
        elif method == 'drop':
            # Remove rows with missing values in this column
            data = [row for row in data if row.get(col, '').strip()]
    
    # Update stored data
    data_store[session_id]['data'] = data
    data_store[session_id]['operations'].append({
        'type': 'impute_missing',
        'method': method,
        'columns': columns_to_impute,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'message': f'Successfully imputed missing values using {method} method',
        'new_shape': [len(data), len(data_store[session_id]['columns'])],
        'missing_values': 'Updated'
    })

# For Vercel serverless deployment
def main(request):
    return handler(request)