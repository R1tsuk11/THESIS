"""
Test script for running the Arami application with Android simulation.
This script finds an available port, then launches the app with Android simulation.
It ensures proper audio recording setup for mobile platforms.
"""

import os
import sys
import subprocess
import socket
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure flet_audio_recorder is available
def check_flet_audio_recorder():
    """Check and install flet_audio_recorder if needed."""
    try:
        import flet_audio_recorder
        logger.info(f"flet_audio_recorder is available: {getattr(flet_audio_recorder, '__file__', 'unknown')}")
        return True
    except ImportError:
        logger.warning("flet_audio_recorder not found, attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flet_audio_recorder"])
            logger.info("Successfully installed flet_audio_recorder")
            return True
        except Exception as e:
            logger.error(f"Failed to install flet_audio_recorder: {e}")
            return False

def is_port_available(port):
    """Check if a port is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except Exception as e:
            logger.debug(f"Port {port} unavailable: {e}")
            return False

def find_available_port():
    """Find an available port to use."""
    # First try some specific ports
    for port in [8550, 8551, 8552, 8553, 8554, 8560, 8570, 8580, 8590]:
        if is_port_available(port):
            logger.info(f"Found available port: {port}")
            return port
    
    # Then try some random ports
    for _ in range(5):
        port = random.randint(10000, 65000)
        if is_port_available(port):
            logger.info(f"Found available random port: {port}")
            return port
    
    # If all else fails, return a high random port and hope for the best
    port = random.randint(20000, 65000)
    logger.info(f"Using random high port: {port}")
    return port

def test_audio_recording():
    """Test audio recording with flet_audio_recorder."""
    try:
        logger.info("Testing audio recording with flet_audio_recorder...")
        subprocess.run([sys.executable, 
                      os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "voice_recognition", 
                                   "test_flet_audio_recorder.py"), 
                      "--android"], 
                     check=True)
        logger.info("Audio recording test completed")
        return True
    except Exception as e:
        logger.error(f"Error testing audio recording: {e}")
        return False

def run_app_with_android():
    """Run the Arami application with Android simulation."""
    # First, test audio recording
    logger.info("Testing audio recording before starting the app...")
    test_audio_recording()
    
    # Ensure flet_audio_recorder is available
    check_flet_audio_recorder()
    
    # Find an available port
    port = find_available_port()
    logger.info(f"Using port {port} for Android simulation")
    
    # Prepare command
    command = f"python start_arami.py --port {port} --android"
    logger.info(f"Running command: {command}")
    
    # Run the command
    try:
        process = subprocess.Popen(command, shell=True)
        logger.info(f"Started application with PID: {process.pid}")
        print(f"\nApplication started on port {port} with Android simulation.")
        print("Close this window to stop the application.")
        
        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        process.terminate()
    except Exception as e:
        logger.error(f"Error running application: {e}")
        
        # Fallback to flet run
        try:
            fallback_command = f"flet run start_arami.py --port {port} --android"
            logger.info(f"Trying fallback command: {fallback_command}")
            fallback_process = subprocess.Popen(fallback_command, shell=True)
            fallback_process.wait()
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")

if __name__ == "__main__":
    logger.info("Starting Arami Waray with Android simulation")
    
    # Set the environment variable for Android simulation
    os.environ['SIMULATE_ANDROID'] = 'true'
    
    # Check and install flet_audio_recorder if needed
    check_flet_audio_recorder()
    
    # Run the app
    run_app_with_android()
