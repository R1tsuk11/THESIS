#!/bin/bash

echo "Running port availability test..."
python test_android_port.py

echo ""
echo "Starting Arami with Android simulation..."
PORT=$(cat available_port.txt)
echo "Using port $PORT"

echo ""
echo "Running: python start_arami.py --port $PORT --android"
python start_arami.py --port $PORT --android

echo ""
echo "If the app didn't start, try running:"
echo "flet run start_arami.py --port $PORT --android"
