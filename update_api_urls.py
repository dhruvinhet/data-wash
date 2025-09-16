import os
import re

def update_api_urls():
    """Update all localhost API URLs to use the config file"""
    
    components_dir = "frontend/src/components"
    files_to_update = [
        "DataVisualization.js",
        "DataTypeInfo.js", 
        "DatasetDescription.js",
        "DataEncoding.js",
        "ColumnStandardization.js",
        "OutlierRemoval.js",
        "DuplicateRowRemoval.js",
        "SkewnessTransformation.js",
        "DataValidation.js",
        "Finalize.js"
    ]
    
    for filename in files_to_update:
        filepath = os.path.join(components_dir, filename)
        if os.path.exists(filepath):
            print(f"Updating {filename}...")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add import if not already present
            if "import API_BASE_URL from '../config';" not in content:
                content = re.sub(
                    r"(import.*from ['\"]axios['\"];)",
                    r"\1\nimport API_BASE_URL from '../config';",
                    content
                )
            
            # Replace localhost URLs
            content = re.sub(
                r"'http://localhost:5000/api/([^']+)'",
                r"`${API_BASE_URL}/\1`",
                content
            )
            
            # Replace double-quoted URLs too
            content = re.sub(
                r'"http://localhost:5000/api/([^"]+)"',
                r'`${API_BASE_URL}/\\1`',
                content
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {filename}")
        else:
            print(f"⚠️  File not found: {filename}")

if __name__ == "__main__":
    update_api_urls()
    print("\n🎉 All API URLs updated for Vercel deployment!")