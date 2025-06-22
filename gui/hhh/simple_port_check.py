import socket
import random

def is_port_available(port):
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except Exception as e:
        print(f"Port {port} unavailable: {e}")
        return False

def find_available_port():
    """Find an available port in the range."""
    # Check common Flet ports first
    common_ports = [8550, 8551, 8552, 8553, 8554]
    print("\nChecking common Flet ports:")
    for port in common_ports:
        available = is_port_available(port)
        print(f"Port {port}: {'Available' if available else 'IN USE'}")
        if available:
            return port
    
    # Check other ports
    for port in range(8000, 9000, 100):
        available = is_port_available(port)
        if available:
            print(f"Found available port: {port}")
            return port
    
    # Try random high port
    port = random.randint(10000, 65000)
    print(f"Using random high port: {port}")
    return port

if __name__ == "__main__":
    print("===== Simple Port Checker =====")
    
    # Find an available port
    port = find_available_port()
    print(f"\nRECOMMENDED PORT: {port}")
    print(f"Run the app with: python start_arami.py --port {port} --android")
    
    # Write port to file
    with open("available_port.txt", "w") as f:
        f.write(str(port))
    print(f"Port written to available_port.txt")
