
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import after environment variables are loaded
from server.app import create_app

if __name__ == '__main__':
    app = create_app()
    # Use different port than Node.js server
    port = int(os.getenv('FLASK_PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
