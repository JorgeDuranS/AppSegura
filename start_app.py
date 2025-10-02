#!/usr/bin/env python3
"""
Robust application starter script
Handles initialization and graceful error recovery
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main startup function with error handling"""
    print("🚀 Starting Secure Web Application...")
    print("=" * 50)
    
    # Change to the correct directory
    app_dir = Path(__file__).parent
    backend_dir = app_dir / "backend"
    src_dir = backend_dir / "src"
    
    if not src_dir.exists():
        print("❌ Error: backend/src directory not found")
        print(f"   Current directory: {app_dir}")
        print("   Make sure you're running this from the application root directory")
        return 1
    
    # Step 1: Run initialization
    print("🔧 Step 1: Initializing application components...")
    try:
        result = subprocess.run([
            sys.executable, "init_app.py"
        ], cwd=src_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Initialization failed:")
            print(result.stderr)
            print("\n💡 Trying manual recovery...")
            
            # Manual recovery attempt
            try:
                sys.path.insert(0, str(src_dir))
                from init_app import main as init_main
                if not init_main():
                    print("❌ Manual recovery also failed")
                    return 1
                print("✅ Manual recovery successful")
            except Exception as e:
                print(f"❌ Manual recovery failed: {e}")
                return 1
        else:
            print("✅ Initialization successful")
            print(result.stdout)
    
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return 1
    
    # Step 2: Start the application
    print("🌐 Step 2: Starting Flask application...")
    try:
        # Check if we should use development or production mode
        env = os.environ.get('FLASK_ENV', 'development')
        
        if env == 'development':
            print("🔧 Running in development mode")
            print("📍 Application will be available at: http://localhost:5000")
            print("🛑 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Run the Flask app
            subprocess.run([sys.executable, "app.py"], cwd=src_dir)
        else:
            print("🏭 Running in production mode")
            print("📍 Application will be available at: http://localhost:8000")
            print("🛑 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Run with waitress for production
            try:
                subprocess.run([
                    sys.executable, "-m", "waitress", 
                    "--host=127.0.0.1", "--port=8000", 
                    "app:app"
                ], cwd=src_dir)
            except FileNotFoundError:
                print("⚠️  Waitress not found, falling back to development server")
                subprocess.run([sys.executable, "app.py"], cwd=src_dir)
    
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())