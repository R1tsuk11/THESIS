"""
Simple entry point for the Arami application that ensures all modules
are properly loaded and initialized before starting the app.
"""

import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the necessary paths to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

def init():
    """Initialize all required components."""
    logger.info("Initializing Arami application...")
    
    # Check for Android environment
    is_android = 'ANDROID_DATA' in os.environ
    logger.info(f"Running on Android: {is_android}")
    
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
                    from audio_recorder import recorder_manager
                    logger.info("Imported recorder_manager from direct path")
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
    
    # Import and run the main app
    try:
        import flet as ft
        import viewhandler
        import random
        import socket
        
        # Try to find an available port
        def is_port_available(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return True
                except Exception as e:
                    logger.debug(f"Port {port} unavailable: {e}")
                    return False
        
        # Try a few different ports
        ports_to_try = [0] + list(range(8000, 8100)) + [random.randint(10000, 65000) for _ in range(5)]
        
        for port in ports_to_try:
            if port == 0 or is_port_available(port):
                logger.info(f"Starting Flet app on port {port if port != 0 else 'auto'}")
                try:
                    # Use port=0 to auto-select an available port, or a specific port
                    # Set view=None to prevent opening a browser window (it starts desktop app instead)
                    ft.app(target=viewhandler.main, port=port, view=None)
                    break  # If we reach here, the app started successfully
                except Exception as e:
                    logger.error(f"Error starting app on port {port}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    if port == ports_to_try[-1]:
                        raise  # Re-raise the exception if we've tried all ports
        else:
            logger.error("Could not find an available port. Try closing other applications.")
            return False
    except ImportError as e:
        logger.error(f"Could not import viewhandler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Try with different path
        try:
            import flet as ft
            import random
            import socket
            from gui.hhh import viewhandler
            
            # Try a random port to avoid conflicts
            port = random.randint(10000, 65000)
            logger.info(f"Starting Flet app on port {port}")
            ft.app(target=viewhandler.main, port=port, view=None)
        except ImportError as e:
            logger.error(f"Failed to import viewhandler from gui.hhh: {e}")
            return False
        except Exception as e:
            logger.error(f"Error starting app: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting Arami Waray application...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Initialize components
    init()
    
    # Start the app
    success = start_app()
    if not success:
        logger.error("Failed to start the application. Please check your installation.")
