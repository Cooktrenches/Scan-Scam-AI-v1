"""
WSGI configuration for PythonAnywhere
Copy this content to your WSGI configuration file in PythonAnywhere Web tab
"""
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/Scan-Beta-V1'  # REPLACE YOUR_USERNAME
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Import Flask app
from web_app import app as application
