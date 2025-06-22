import os
import sys
import socket
import logging
import subprocess
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_process_using_port(port):
    """Get the process ID using a specific port."""
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                process_info = subprocess.check_output(f'tasklist /fi "PID eq {pid}"', shell=True).decode()
                                process_lines = process_info.split('\n')
                                if len(process_lines) > 3:
                                    return f"PID {pid}: {process_lines[3]}"
                                else:
                                    return f"PID {pid}: Unknown"
                            except:
                                return f"PID {pid}"
            return "No process found"
        except Exception as e:
            return f"Could not determine process: {str(e)}"
    else:
        try:
            output = subprocess.check_output(f"lsof -i :{port} | grep LISTEN", shell=True).decode()
            return output.strip() if output else "No process found"
        except:
            return "Could not determine process"

def check_flet_ports():
    """Check common Flet ports."""
    flet_ports = [8550, 8551, 8552, 8553, 8554, 8000, 8080]
    print("\nChecking common Flet ports:")
    for port in flet_ports:
        in_use = check_port_in_use(port)
        status = "IN USE" if in_use else "Available"
        print(f"Port {port}: {status}")
        if in_use:
            process = get_process_using_port(port)
            print(f"  Used by: {process}")

def get_recommended_port():
    """Find an available port."""
    for port in range(8000, 9000, 10):
        if not check_port_in_use(port):
            return port
    return None

if __name__ == "__main__":
    print("===== Port Diagnostic Tool =====")
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    # Check common Flet ports
    check_flet_ports()
    
    # Get recommended port
    recommended_port = get_recommended_port()
    if recommended_port:
        print(f"\nRECOMMENDED: Use port {recommended_port}")
        print(f"Run: python start_arami.py --port {recommended_port} --android")
        
        # Save to file for batch scripts
        with open("available_port.txt", "w") as f:
            f.write(str(recommended_port))
    else:
        print("\nCould not find an available port in the common range.")
        print("Try manually specifying a high port number, e.g., --port 50000")
    
    print("\nTo kill a process using a specific port (Windows):")
    print("1. Run 'netstat -ano | findstr :PORT' to find the PID")
    print("2. Run 'taskkill /F /PID PID_NUMBER' to kill the process")
