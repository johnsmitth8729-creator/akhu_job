# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Ensure the uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the application
    print("Starting Al-Khwarizmi University Recruitment Portal...")
    app.run(host='0.0.0.0', port=5000, debug=True)
