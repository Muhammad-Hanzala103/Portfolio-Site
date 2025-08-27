from dotenv import load_dotenv
import os

load_dotenv()

from my_marketplace.app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)