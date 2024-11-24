#!/bin/bash

# Start the Flask data service
echo "Starting Flask data service..."
python data_service.py &
FLASK_DS_PID=$!

# Start the Flask backend service
echo "Starting Flask backend service..."
python backend_serice.py &
FLASK_PID=$!

# Start the Dash app
echo "Starting Plotly Dash app..."
python app.py &
DASH_PID=$!

# Wait for all services to start
sleep 2

echo "Services started successfully."
echo "Flask data service PID: $FLASK_DS_PID"
echo "Flask backend PID: $FLASK_PID"
echo "Dash app PID: $DASH_PID"

# Function to clean up on exit
cleanup() {
  echo "Stopping services..."
  kill $FLASK_PID
  kill $DASH_PID
  kill $FLASK_DS_PID
  echo "Services stopped."
}

# Trap SIGINT and SIGTERM to clean up processes on exit
trap cleanup SIGINT SIGTERM

# Keep the script running to allow manual termination
wait

