"""
Simple script to list all installed Python packages for debugging.
"""

import os
import sys
import pkg_resources
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_installed_packages():
    """List all installed packages and their versions."""
    logger.info("===== Installed Python Packages =====")
    
    # Get all installed packages
    packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
    
    # Print them
    for pkg in packages:
        logger.info(pkg)
    
    # Check specifically for audio-related packages
    audio_packages = [pkg for pkg in packages if any(term in pkg.lower() for term in ['audio', 'sound', 'voice', 'speech', 'record', 'flet'])]
    
    logger.info("\n===== Audio-Related Packages =====")
    for pkg in audio_packages:
        logger.info(pkg)
    
    # Check for specific packages
    required_packages = ['flet', 'flet_audio', 'flet_audio_recorder', 'PyAudio', 'SpeechRecognition', 'pydub']
    
    logger.info("\n===== Required Packages =====")
    for pkg_name in required_packages:
        try:
            pkg = pkg_resources.get_distribution(pkg_name)
            logger.info(f"{pkg.key}=={pkg.version} (INSTALLED)")
        except pkg_resources.DistributionNotFound:
            logger.warning(f"{pkg_name} (NOT INSTALLED)")

if __name__ == "__main__":
    logger.info("Listing installed Python packages for debugging")
    list_installed_packages()
