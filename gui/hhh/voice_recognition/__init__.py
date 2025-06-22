"""
Voice recognition module for Arami application
"""

# Make important components available at package level
try:
    from .audio_recorder import recorder_manager
    from .speech_recognition_utils import SpeechProcessor, capture_audio
    from .audio_processing import enhance_audio_for_waray, extract_features
except ImportError:
    pass  # When used outside package structure
