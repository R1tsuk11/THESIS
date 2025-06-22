@echo off
echo Testing audio recording on Android simulation...

echo 1. Testing all audio recording methods:
python test_audio_recording.py --android

echo.
echo 2. Testing flet_audio_recorder integration:
python test_android_audio.py --android

echo.
echo If you want to run the full application with Android simulation, run:
echo python test_android_run.py
