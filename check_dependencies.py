#!/usr/bin/env python3
"""
Dependency Checker for Elasticsearch Sensor Dashboard
This script checks if all required Python dependencies are installed correctly.
"""

import sys
import pkg_resources

required_packages = [
    "elasticsearch",
    "python-dotenv",
    "flask",
    "requests",
    "pandas",
    "urllib3",
    "gunicorn"
]

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    installed = {}
    
    for package in required_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            installed[package] = version
        except pkg_resources.DistributionNotFound:
            missing.append(package)
    
    return missing, installed

def main():
    """Main function."""
    print("Checking Elasticsearch Sensor Dashboard dependencies...")
    missing, installed = check_dependencies()
    
    if missing:
        print("\n❌ Missing packages:")
        for package in missing:
            print(f"  - {package}")
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements-elasticsearch.txt")
        print("  OR")
        print("  ./install_dependencies.sh")
        return 1
    else:
        print("\n✅ All required packages are installed:")
        for package, version in installed.items():
            print(f"  - {package}: {version}")
        return 0

if __name__ == "__main__":
    sys.exit(main())