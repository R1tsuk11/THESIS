"""
Script to check what's available in the flet_audio_recorder module.
"""

import sys
import importlib

def check_module(module_name):
    """Check and display details about a module."""
    print(f"\nChecking module: {module_name}")
    try:
        # Import the module
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)
        
        # Print module details
        print(f"  Module file: {getattr(module, '__file__', 'unknown')}")
        print(f"  Module version: {getattr(module, '__version__', 'unknown')}")
        
        # Print attributes and methods
        print("\n  Available attributes and methods:")
        for attr in dir(module):
            if not attr.startswith('__'):
                value = getattr(module, attr)
                type_str = type(value).__name__
                print(f"    - {attr}: {type_str}")
                
                # If it's a class, show its methods too
                if type_str == 'type':
                    print(f"      Class methods:")
                    for class_attr in dir(value):
                        if not class_attr.startswith('__'):
                            print(f"        - {class_attr}")
        
        return True
    except ImportError as e:
        print(f"  Error importing {module_name}: {e}")
        return False
    except Exception as e:
        print(f"  Error examining {module_name}: {e}")
        return False

if __name__ == "__main__":
    # Check audio-related modules
    modules_to_check = [
        "flet_audio_recorder",
        "flet_audio",
        "speech_recognition"
    ]
    
    for module in modules_to_check:
        check_module(module)
