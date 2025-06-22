import os
import sys
import socket
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_port_available(port):
    """Check if a port is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except Exception as e:
            logger.info(f"Port {port} unavailable: {e}")
            return False

def find_available_port(start_range=8000, end_range=9000, num_random=5):
    """Find an available port to use."""
    # First try some specific ports
    for port in range(start_range, end_range, 10):
        if is_port_available(port):
            logger.info(f"Found available port: {port}")
            return port
    
    # Then try some random ports
    for _ in range(num_random):
        port = random.randint(10000, 65000)
        if is_port_available(port):
            logger.info(f"Found available random port: {port}")
            return port
    
    # Finally, let the OS choose a port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        port = s.getsockname()[1]
        logger.info(f"OS assigned port: {port}")
        return port

if __name__ == "__main__":
    logger.info("Testing port availability for Android simulation")
    
    # Check if android flag is provided
    is_android = '--android' in sys.argv
    logger.info(f"Android simulation mode: {is_android}")
    
    # Test if flet's default port is available
    default_port = 8551
    is_default_available = is_port_available(default_port)
    logger.info(f"Default port {default_port} available: {is_default_available}")
    
    # Find an available port
    available_port = find_available_port()
    logger.info(f"Found available port: {available_port}")
    
    # Write port to a file so other processes can use it
    port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "available_port.txt")
    with open(port_file, "w") as f:
        f.write(str(available_port))
    logger.info(f"Wrote available port to {port_file}")
    
    print(f"\nRECOMMENDED: Use port {available_port} for your Flet app")
    print(f"To use this port with Flet, run: flet run start_arami.py --port {available_port} --android")
