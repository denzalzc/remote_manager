import os, subprocess, sys


def depends():
    try:
        python_version = subprocess.check_output(['python3', '--version'], stderr=subprocess.STDOUT).decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[-] Python3 not installed")
        sys.exit(1)
    try:
        result = subprocess.run(['dpkg', '-l', 'python3.12-venv'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[+] python3.12-venv installed")
        else:
            print("[-] python3.12-venv not installed")
            sys.exit(1)
    except FileNotFoundError:
        print("Looks like is not Debian dist")
    
    try:
        pip_version = subprocess.check_output(['pip3', '--version'], stderr=subprocess.STDOUT).decode()
        print(f"[+] pip installed: {pip_version.split()[1]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[-] pip not installed")
        sys.exit(1)
    
    if not os.path.exists('venv'):
        subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)
        print("[+] Virtual environment created")
    else:
        print("[+] Virtual environment already exists")
    
    venv_pip = 'venv/bin/pip'
    if sys.platform == 'win32':
        venv_pip = 'venv\\Scripts\\pip'
    
    if os.path.exists('requirements.txt'):
        subprocess.run([venv_pip, 'install', '-r', 'requirements.txt'], check=True)
        print("[+] Dependencies installed")
    else:
        print("[-] requirements.txt not found")
    
    print("[+][+][+] All python depends are installed")

    return True




depends()
