"""
Simple test script for flet_audio_recorder.
This script demonstrates how to use flet_audio_recorder with a Flet app.
"""

import os
import sys
import time
import flet as ft
from flet_audio_recorder import AudioRecorder

def main(page: ft.Page):
    page.title = "Flet Audio Recorder Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Status text
    status_text = ft.Text("Ready to record", size=20)
    
    # Audio recorder
    recorder = AudioRecorder()
    
    # Add the recorder to the page
    page.add(recorder)
    
    # Update the page
    page.update()
    
    def on_start_recording(e):        status_text.value = "Recording... Speak now!"
        page.update()
        
        # Create a temp file for the recording
        output_path = f"recording_{int(time.time())}.wav"
        
        # Start recording
        recorder.start_recording(output_path=output_path)
    
    def on_stop_recording(e):
        status_text.value = "Stopping recording..."
        page.update()
        
        # Stop recording and get the audio data
        audio_data = recorder.stop_recording()
        
        if audio_data:
            # Save to file
            output_path = f"recording_{int(time.time())}.wav"
            with open(output_path, "wb") as f:
                f.write(audio_data)
            
            status_text.value = f"Recording saved to {output_path}"
            
            # Add a play button for the recording
            page.add(
                ft.ElevatedButton(
                    "Play Recording",
                    on_click=lambda _: page.launch_url(os.path.abspath(output_path))
                )
            )
        else:
            status_text.value = "Failed to get audio data"
            
        page.update()
    
    # Create UI
    page.add(
        status_text,
        ft.Row([
            ft.ElevatedButton("Start Recording", on_click=on_start_recording),
            ft.ElevatedButton("Stop Recording", on_click=on_stop_recording),
        ]),
    )

# Check if simulating Android
if '--android' in sys.argv:
    os.environ['SIMULATE_ANDROID'] = 'true'
    print("Running in Android simulation mode")

# Run the app
ft.app(target=main)
