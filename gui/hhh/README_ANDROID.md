# Running Arami Waray Application with Android Simulation

## Overview

This document explains how to run the Arami Waray language learning application with Android simulation mode to test the app's mobile behavior on desktop.

## Key Changes Made

1. Fixed indentation issue in `audio_recorder.py` - The `__init__` method had incorrect indentation
2. Added proper command-line argument parsing for Android simulation mode
3. Improved port selection logic to avoid port conflicts
4. Created diagnostic tools to find available ports
5. Added batch scripts for easy running with Android simulation

## Running the Application

### Method 1: Using the provided scripts

1. Run the `run_with_android.bat` script (Windows) or `run_with_android.sh` (Linux/Mac):
   ```
   .\run_with_android.bat
   ```

   This script will:
   - Find an available port
   - Set up Android simulation mode
   - Start the application

### Method 2: Running directly with arguments

1. Find an available port using the simple port checker:
   ```
   python simple_port_check.py
   ```

2. Run the application with the recommended port:
   ```
   python start_arami.py --port PORT_NUMBER --android
   ```

### Method 3: Using flet run

If you prefer to use `flet run`, use the following command:
```
flet run start_arami.py --port PORT_NUMBER --android
```

Replace `PORT_NUMBER` with an available port number.

## Troubleshooting

If you encounter port conflicts:

1. Run the port diagnostic tool:
   ```
   python port_diagnostic.py
   ```

2. Close any applications using the conflicting ports

3. Try a different port with:
   ```
   python start_arami.py --port DIFFERENT_PORT --android
   ```

## Known Issues

1. Audio processing module import error - This doesn't prevent the application from running
2. Phoneme analysis error - This is a non-critical error in the speech recognition module

## Testing Audio Recording

The application now successfully records audio and performs speech recognition. The audio recording works in both desktop and Android simulation modes.

## Recommendations

1. Always use the `--android` flag when testing features that should work on mobile
2. Use a specific port with `--port` to avoid conflicts
3. If the application doesn't start, try using the diagnostic tools to find available ports
