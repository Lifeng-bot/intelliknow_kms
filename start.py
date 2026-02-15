#!/usr/bin/env python3
"""
IntelliKnow KMS Startup Script

This script helps you start the IntelliKnow KMS system components.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def print_banner():
    """Print the IntelliKnow KMS banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           IntelliKnow KMS - Gen AI-Powered KMS             ║
    ║                                                           ║
    ║           Knowledge Management System v1.0.0              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")

    required_packages = [
        "fastapi", "uvicorn", "streamlit", "sqlalchemy", 
        "pydantic", "openai", "langchain", "faiss-cpu",
        "PyPDF2", "python-docx", "sentence-transformers"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            # Map pip package names to import names
            import_name = package.replace("-", "_")
            if package == "faiss-cpu":
                import_name = "faiss"
            elif package == "python-docx":
                import_name = "docx"
            elif package == "sentence-transformers":
                import_name = "sentence_transformers"
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages with: pip install -r requirements.txt")
        return False

    print("All dependencies are installed.")
    return True

def check_environment():
    """Check if environment variables are set."""
    print("Checking environment...")

    # Check for .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("Warning: .env file not found. Creating a template...")
        with open(env_file, "w") as f:
            f.write("""# IntelliKnow KMS Environment Configuration

# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Database URL (SQLite by default)
DATABASE_URL=sqlite:///./intelliknow.db

# FAISS Index Path
FAISS_INDEX_PATH=./data/faiss_index
""")
        print("Created .env file. Please update it with your DeepSeek API key.")
        return False

    # Check for DeepSeek API key
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("Error: DEEPSEEK_API_KEY not set in .env file.")
        return False

    print("Environment check passed.")
    return True


def initialize_database():
    """Initialize the database."""
    print("Initializing database...")

    from app.database import init_db
    init_db()

    print("Database initialized successfully.")

def start_backend():
    """Start the FastAPI backend server."""
    print("Starting FastAPI backend server...")

    # Change to project root directory
    os.chdir(project_root)

    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    log_file = logs_dir / f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Open log file
    log_handle = open(log_file, "w", encoding="utf-8")

    # Start uvicorn server with logging
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        stdout=log_handle,
        stderr=subprocess.STDOUT
    )
    
    print(f"Backend logs will be saved to: {log_file}")

    # Check if backend started successfully
    time.sleep(2)
    if backend_process.poll() is not None:
        # Backend process has terminated
        print("Error: Backend server failed to start.")
        return None

    return backend_process

def start_user_interface():
    """Start the Streamlit user interface."""
    print("Starting Streamlit user interface...")

    # Change to project root directory
    os.chdir(project_root)

    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    log_file = logs_dir / f"user_interface_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Open log file
    log_handle = open(log_file, "w", encoding="utf-8")

    # Start streamlit with logging
    user_interface_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/user_interface.py", "--server.port", "8501"],
        stdout=log_handle,
        stderr=subprocess.STDOUT
    )
    
    print(f"User interface logs will be saved to: {log_file}")

    return user_interface_process

def start_admin_interface():
    """Start the Streamlit admin interface."""
    print("Starting Streamlit admin interface...")

    # Change to project root directory
    os.chdir(project_root)

    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    log_file = logs_dir / f"admin_interface_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Open log file
    log_handle = open(log_file, "w", encoding="utf-8")

    # Start streamlit with logging
    admin_interface_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/admin_interface.py", "--server.port", "8502"],
        stdout=log_handle,
        stderr=subprocess.STDOUT
    )
    
    print(f"Admin interface logs will be saved to: {log_file}")

    return admin_interface_process

def main():
    """Main function to start the IntelliKnow KMS system."""
    print_banner()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Initialize database
    initialize_database()

    # Start services
    processes = []

    try:
        # Start backend
        backend_process = start_backend()
        if backend_process is None:
            print("Failed to start backend server. Exiting...")
            sys.exit(1)
        processes.append(("Backend", backend_process))
        print("Backend server started on http://localhost:8000")

        # Wait for backend to start
        time.sleep(3)

        # Start user interface
        user_interface_process = start_user_interface()
        processes.append(("User Interface", user_interface_process))
        print("User interface started on http://localhost:8501")

        # Start admin interface
        admin_interface_process = start_admin_interface()
        processes.append(("Admin Interface", admin_interface_process))
        print("Admin interface started on http://localhost:8502")

        print("\nAll services started successfully!")
        print("Press Ctrl+C to stop all services.")

        # Wait for user to stop the services
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping services...")

        # Terminate all processes
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("All services stopped.")

if __name__ == "__main__":
    main()
