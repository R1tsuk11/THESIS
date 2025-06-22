"""
Test port binding and socket issues in Flet
"""
import socket
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ports():
    """Test binding to different ports to find available ones"""
    logger.info("Testing port availability...")
    
    ports_to_try = [8551] + list(range(8000, 8010)) + [random.randint(10000, 65000) for _ in range(5)]
    available_ports = []
    
    for port in ports_to_try:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                available_ports.append(port)
                logger.info(f"Port {port} is available")
        except Exception as e:
            logger.info(f"Port {port} is NOT available: {e}")
    
    if available_ports:
        logger.info(f"Available ports: {available_ports}")
        return available_ports[0]
    else:
        logger.error("No available ports found!")
        return None

if __name__ == "__main__":
    available_port = test_ports()
    if available_port:
        logger.info(f"Recommended port to use: {available_port}")
        
        # Test creating a real socket server
        try:
            logger.info(f"Testing socket server on port {available_port}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('localhost', available_port))
            s.listen(1)
            logger.info(f"Successfully started socket server on port {available_port}")
            s.close()
        except Exception as e:
            logger.error(f"Failed to create socket server: {e}")
