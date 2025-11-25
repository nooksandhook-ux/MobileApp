#!/usr/bin/env python3
"""
Nhooks Mobile Backend - Development Server
Run this file to start the Flask development server
"""

from app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║         Nhooks Mobile Backend API Server                 ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Server running on: http://{host}:{port}              ║
    ║  Health check: http://{host}:{port}/api/health       ║
    ║  Debug mode: {debug}                                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=host, port=port, debug=debug)
