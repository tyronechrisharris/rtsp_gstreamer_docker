#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/config.json"
PYTHON_CMD=python3 # Assuming python3 is available for parsing config

# Default image name (you can change this)
DOCKER_IMAGE_NAME="rtsp-clock-server:latest"

# Function to read JSON value (basic, needs jq for robust parsing if available)
get_json_value() {
    local json_file="$1"
    local key="$2"
    # Basic parsing if jq is not installed
    if command -v jq &> /dev/null; then
        jq -r ".$key" "$json_file"
    else
        # Fallback for simple cases, might not handle all JSON complexities
        grep -o "\"$key\": *\"?[^\",]*\"?" "$json_file" | sed -E "s/\"$key\": *\"?([^\",]*)\"?/\1/" | head -n 1
    fi
}


# Check if config.json exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: config.json not found in $SCRIPT_DIR."
    echo "Please create it. You can run 'python3 app/config_loader.py' in the app directory to generate a default one locally."
    exit 1
fi

# Read serverPort from config.json to map it correctly
SERVER_PORT=$(get_json_value "$CONFIG_FILE" "serverPort")
if [ -z "$SERVER_PORT" ] || ! [[ "$SERVER_PORT" =~ ^[0-9]+$ ]]; then
    echo "Warning: Could not reliably parse 'serverPort' from config.json. Defaulting to 8554 for port mapping."
    SERVER_PORT=8554
fi
echo "Attempting to map host port $SERVER_PORT to container port $SERVER_PORT (RTSP)."

# Build the Docker image if it doesn't exist (optional, you can pre-build)
if [[ "$(docker images -q $DOCKER_IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image $DOCKER_IMAGE_NAME not found. Building..."
  docker build -t $DOCKER_IMAGE_NAME .
  if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
  fi
fi

echo "Starting RTSP Clock Server in Docker container..."
echo "Configuration will be read from: $CONFIG_FILE"
echo "Stream should be available at: rtsp://<your_host_ip>:$SERVER_PORT$(get_json_value "$CONFIG_FILE" "rtspStreamPath")"
if [ -n "$(get_json_value "$CONFIG_FILE" "viewerUsername")" ]; then
    echo "Username: $(get_json_value "$CONFIG_FILE" "viewerUsername")"
fi


# Run the Docker container
# -it for interactive mode (logs to console), --rm to remove container on exit
# Mount config.json read-only
# Map the RTSP port
docker run -it --rm \
    --name rtsp-clock-app \
    -v "$CONFIG_FILE":/app/config.json:ro \
    -p "$SERVER_PORT":"$SERVER_PORT"/tcp \
    -p "$SERVER_PORT":"$SERVER_PORT"/udp \
    $DOCKER_IMAGE_NAME

echo "RTSP Clock Server container stopped."