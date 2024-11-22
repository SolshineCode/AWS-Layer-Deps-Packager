import os
import zipfile
import shutil
import subprocess
import sys
import platform

# Step 1: Define the script and target file paths
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
requirements_path = os.path.join(script_dir, 'requirements.txt')

print(f"Script directory: {script_dir}")
print(f"Expected requirements.txt path: {requirements_path}")

# Step 2: Check if requirements.txt exists
if os.path.exists(requirements_path):
    print("requirements.txt found")
else:
    print("requirements.txt not found")

# Step 3: Create a package directory
package_dir = os.path.join(script_dir, 'package')
if os.path.exists(package_dir):
    shutil.rmtree(package_dir)
os.makedirs(package_dir)
print(f"Created package directory: {package_dir}")

# Step 4: Install dependencies with platform-specific options
if os.path.exists(requirements_path):
    print("Installing dependencies...")
    try:
        # Base pip command
        pip_command = [
            sys.executable, '-m', 'pip', 'install',
            '-r', requirements_path,
            '-t', package_dir,
            '--platform', 'manylinux2014_x86_64',  # Target platform for Lambda
            '--implementation', 'cp',  # CPython
            '--python-version', '3.9',  # Target Python version
            '--only-binary=:all:',  # Prefer wheels
            '--no-deps'  # Install only the package, not its dependencies
        ]
        
        # First pass: try to install everything with manylinux wheels
        result = subprocess.run(
            pip_command,
            check=False,  # Don't raise exception on error
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Some packages couldn't be installed with manylinux wheels. Trying source installation...")
            # Second pass: install packages that failed without platform restrictions
            pip_command = [
                sys.executable, '-m', 'pip', 'install',
                '-r', requirements_path,
                '-t', package_dir,
                '--no-cache-dir'  # Avoid using cached wheels
            ]
            result = subprocess.run(
                pip_command,
                check=True,
                capture_output=True,
                text=True
            )
        
        print("Dependencies installed successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to install dependencies:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)
else:
    print("Could not install dependencies: requirements.txt not found")

# Step 5: Create the deployment package
zip_path = os.path.join(script_dir, 'deployment_package.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(package_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, package_dir)
            # Skip unnecessary files
            if not any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.dist-info']):
                zipf.write(file_path, arcname)
                print(f"Added to zip: {arcname}")

print(f"Deployment package created: {zip_path}")

# Step 6: Clean up
shutil.rmtree(package_dir)
print("Cleaned up package directory")
