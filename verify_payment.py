import sys
import os

# Add the project directory to the python path
sys.path.append(os.getcwd())

try:
    from app import app
    print("Successfully imported app")
    
    # Check if payment blueprint is registered
    if 'payment' in app.blueprints:
        print("Payment blueprint is registered")
    else:
        print("ERROR: Payment blueprint is NOT registered")
        sys.exit(1)
        
    print("Verification successful!")
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
