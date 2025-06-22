"""
Simple entry point for the Arami application that ensures all modules
are properly loaded and initialized before starting the app.
"""

import os
import sys
import importlib
import logging
import random
import socket
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the necessary paths to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Arami Waray language learning application")
    parser.add_argument("--android", action="store_true", help="Run in Android simulation mode")
    parser.add_argument("--port", type=int, help="Port to run the application on")
    
    # Parse only known args to avoid conflicts with other arguments (like from flet)
    args, unknown = parser.parse_known_args()
    return args

def is_port_available(port):
    """Check if a port is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except Exception as e:
            logger.debug(f"Port {port} unavailable: {e}")
            return False

def find_available_port(start_range=8000, end_range=9000, num_random=5):
    """Find an available port to use."""
    # Try a few specific ports first
    specific_ports = [8550, 8551, 8552, 8553, 8554, 8555, 8556]
    for port in specific_ports:
        if is_port_available(port):
            logger.info(f"Found available specific port: {port}")
            return port
    
    # Then try some ports in a range
    for port in range(start_range, end_range, 10):
        if is_port_available(port):
            logger.info(f"Found available port in range: {port}")
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

def init():
    """Initialize all required components."""
    logger.info("Initializing Arami application...")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Check for Android environment or simulation
    is_android = 'ANDROID_DATA' in os.environ or args.android
    os.environ['SIMULATE_ANDROID'] = 'true' if is_android else 'false'
    logger.info(f"Running on Android (real or simulated): {is_android}")
    
    # Import and initialize voice recognition components
    try:
        # First try to import the audio recorder manager
        try:
            from gui.hhh.voice_recognition.audio_recorder import recorder_manager
            logger.info("Imported recorder_manager from gui.hhh.voice_recognition")
        except ImportError:
            try:
                from voice_recognition.audio_recorder import recorder_manager
                logger.info("Imported recorder_manager from voice_recognition")
            except ImportError:
        # Try with modified path
                voice_recog_path = os.path.join(current_dir, "voice_recognition")
                if os.path.exists(voice_recog_path):
                    sys.path.insert(0, voice_recog_path)
                    try:
                        from audio_recorder import recorder_manager
                        logger.info("Imported recorder_manager from direct path")
                    except ImportError:
                        logger.warning("Could not import audio_recorder even with voice_recognition in path")
                        recorder_manager = None
                else:
                    logger.warning(f"Voice recognition path not found: {voice_recog_path}")
                    recorder_manager = None
        
        if recorder_manager:
            initialized = recorder_manager.initialize()
            logger.info(f"Audio recorder manager initialized: {initialized}")
            
            # Make available globally
            sys.modules['global_recorder_manager'] = recorder_manager
            logger.info("Recorder manager registered globally")
    except Exception as e:
        logger.error(f"Error initializing audio recorder: {e}")
        import traceback
        logger.error(traceback.format_exc())

def start_app():
    """Start the Arami application."""
    logger.info("Starting Arami application...")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Import and run the main app
    try:
        import flet as ft
        import viewhandler
        
        # If a specific port was requested, use it
        if args.port:
            port = args.port
            logger.info(f"Using requested port: {port}")
            if not is_port_available(port):
                logger.warning(f"Requested port {port} is not available, finding another...")
                port = find_available_port()
        else:
            # Find an available port
            port = find_available_port()
            
        logger.info(f"Starting Flet app on port {port}")
        
        # Try to run the app
        try:
            # Set view=None to prevent opening a browser window (it starts desktop app instead)
            ft.app(target=viewhandler.main, port=port, view=None)
            logger.info("Flet app started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting app on port {port}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try one more time with a random port
            try:
                port = random.randint(10000, 65000)
                logger.info(f"Trying one more time with random port {port}")
                ft.app(target=viewhandler.main, port=port, view=None)
                return True
            except Exception as e2:
                logger.error(f"Error on second attempt with port {port}: {e2}")
                return False
    except ImportError as e:
        logger.error(f"Could not import viewhandler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Try with different path
        try:
            import flet as ft
            from gui.hhh import viewhandler
            
            # Find a port
            port = find_available_port()
            logger.info(f"Starting Flet app with alternative import on port {port}")
            ft.app(target=viewhandler.main, port=port, view=None)
            return True
        except ImportError as e:
            logger.error(f"Failed to import viewhandler from gui.hhh: {e}")
            return False
        except Exception as e:
            logger.error(f"Error starting app: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

if __name__ == "__main__":
    logger.info("Starting Arami Waray application...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Command line arguments: {sys.argv}")
    
    # Parse arguments
    args = parse_arguments()
    logger.info(f"Android simulation mode: {args.android}")
    logger.info(f"Requested port: {args.port}")
    
    # Initialize components
    init()
    
    # Start the app
    success = start_app()
    if not success:
        logger.error("Failed to start the application. Please check your installation.")
        # Print instructions for troubleshooting
        print("\nTROUBLESHOOTING:")
        print("1. Try running with a specific port: python start_arami.py --port 9000")
        print("2. Run the port test script: python test_android_port.py")
        print("3. Check if any other applications are using the same port")
        print("4. Make sure flet and all dependencies are installed correctly")
        sys.exit(1)
