from app import create_app
import os

app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # Get debug and host settings from environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    app.run(host=host, port=port, debug=debug_mode)
