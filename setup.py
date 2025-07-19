#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News GPT v2 - Cross-platform setup script (2025.07.20 Optimized)
Automatically set up project environment on new PC.

Supported OS: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
Python: 3.10+ (recommended: 3.11+)
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description="", suppress_output=False):
    """Execute command and show result"""
    print(f"[Execute] {description if description else command}")
    try:
        if suppress_output:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
        if result.stdout and not suppress_output:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr and not suppress_output:
            print(f"Error detail: {e.stderr.strip()}")
        return False

def check_python():
    """Check Python version"""
    print("=" * 50)
    print("🐍 Python Environment Check")
    print("=" * 50)
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required.")
        print("💡 Download latest version from https://python.org")
        return False
    
    if version.minor >= 11:
        print("✅ Python 3.11+ optimized version detected")
    else:
        print("⚠️ Python 3.11+ recommended (current version compatible)")
    
    print("✅ Python version check complete")
    return True

def setup_venv():
    """Virtual environment setup"""
    print("\n🔧 Virtual Environment Setup")
    print("-" * 30)
    
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists.")
    else:
        if run_command("python -m venv venv", "Create virtual environment"):
            print("✅ Virtual environment created successfully")
        else:
            return False
    
    # Display virtual environment activation command
    system = platform.system()
    if system == "Windows":
        activate_cmd = "venv\\Scripts\\activate.bat"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print(f"💡 Virtual environment activation command: {activate_cmd}")
    return True

def install_packages():
    """Package installation"""
    print("\n📦 Package Installation")
    print("-" * 30)
    
    # Upgrade pip
    system = platform.system()
    if system == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    if run_command(f"{pip_cmd} install --upgrade pip", "Upgrade pip"):
        print("✅ pip upgrade complete")
    
    # Install requirements.txt
    if os.path.exists("requirements.txt"):
        if run_command(f"{pip_cmd} install -r requirements.txt", "Install packages"):
            print("✅ All packages installed successfully")
            return True
    else:
        print("❌ requirements.txt file not found.")
    
    return False

def check_env_file():
    """환경 설정 파일 확인 및 생성"""
    print("\n🔑 환경 설정 확인")
    print("-" * 30)
    
    if os.path.exists(".env"):
        print("✅ .env 파일이 존재합니다.")
        # .env 파일 내용 간단 검증
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
            required_keys = ["DEEPSEARCH_API_KEY", "AZURE_OPENAI_API_KEY"]
            missing_keys = []
            
            for key in required_keys:
                if f"{key}=your_" in content or key not in content:
                    missing_keys.append(key)
            
            if missing_keys:
                print(f"⚠️ Please configure these API keys: {', '.join(missing_keys)}")
            else:
                print("✅ Required API keys are configured.")
                
    elif os.path.exists(".env.template"):
        print("💡 Copying .env.template to .env...")
        try:
            import shutil
            shutil.copy(".env.template", ".env")
            print("✅ .env file created.")
            print("⚠️ Please open .env file and replace with actual API keys:")
            print("   - DEEPSEARCH_API_KEY (required)")
            print("   - AZURE_OPENAI_API_KEY (required)")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    else:
        print("⚠️ No environment configuration file found.")
        print("💡 Please create .env file and configure these keys:")
        print("   DEEPSEARCH_API_KEY=your_key_here")
        print("   AZURE_OPENAI_API_KEY=your_key_here")
        print("   AZURE_OPENAI_ENDPOINT=your_endpoint_here")

def test_installation():
    """Installation test and server readiness check"""
    print("\n🧪 Installation Test")
    print("-" * 30)
    
    system = platform.system()
    if system == "Windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    # Core package import tests
    test_imports = [
        ("fastapi", "Web Framework"),
        ("uvicorn", "Web Server"), 
        ("openai", "AI API"),
        ("requests", "HTTP Client"),
        ("dotenv", "Environment Config"),
        ("pandas", "Data Processing")
    ]
    
    failed_tests = []
    for package, description in test_imports:
        if run_command(f'{python_cmd} -c "import {package}; print(f\'{package} OK\')"', 
                      f"{package} ({description}) test", suppress_output=True):
            print(f"✅ {package} - {description}")
        else:
            print(f"❌ {package} - {description}")
            failed_tests.append(package)
    
    if failed_tests:
        print(f"\n❌ Failed packages: {', '.join(failed_tests)}")
        print("💡 Try reinstalling with this command:")
        print(f"   {python_cmd} -m pip install {' '.join(failed_tests)}")
        return False
    
    # Check main.py exists
    if os.path.exists("main.py"):
        print("✅ main.py server file confirmed")
    else:
        print("❌ main.py file not found.")
        return False
    
    print("✅ All packages and files test passed")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 News GPT v2 - Automated Environment Setup (2025.07.20 Optimized)")
    print("=" * 60)
    
    # Check Python version
    if not check_python():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_venv():
        print("❌ Virtual environment setup failed")
        sys.exit(1)
    
    # Install packages
    if not install_packages():
        print("❌ Package installation failed")
        sys.exit(1)
    
    # Check environment configuration file
    check_env_file()
    
    # Test installation
    if not test_installation():
        print("❌ Installation test failed")
        sys.exit(1)
    
    # Completion message
    print("\n" + "=" * 60)
    print("🎉 Environment setup completed successfully!")
    print("=" * 60)
    
    system = platform.system()
    if system == "Windows":
        print("🚀 How to run the server:")
        print("  Method 1 (automatic): start_server.bat")
        print("  Method 2 (manual): venv\\Scripts\\activate.bat && python main.py")
    else:
        print("🚀 How to run the server:")
        print("  source venv/bin/activate && python main.py")
    
    print(f"\n🌐 Open http://localhost:8000 in your browser to verify.")
    print("\n📋 Next steps:")
    print("  1. Configure API keys in .env file")
    print("  2. Run the server")
    print("  3. Test keyword analysis in web interface")
    
    # Provide auto-run option on Windows
    if system == "Windows":
        try:
            response = input("\nWould you like to start the server now? (y/N): ").lower()
            if response == 'y':
                print("Starting server...")
                os.system("start_server.bat")
        except KeyboardInterrupt:
            print("\nSetup complete!")

if __name__ == "__main__":
    main()
