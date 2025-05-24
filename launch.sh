#!/bin/bash

# --- Configuration Section ---
# Edit these values to configure your RTSP server
# These will be passed as environment variables to the Docker container.

RTSP_VIEWER_USERNAME=""
RTSP_VIEWER_PASSWORD=""
# RTSP_SERVER_IP should generally be 0.0.0.0 for Docker to listen on all interfaces
RTSP_SERVER_IP="0.0.0.0"
RTSP_SERVER_PORT="8554"
RTSP_VIDEO_CODEC="h264" # "mjpeg" or "h264"
RTSP_VIDEO_RESOLUTION="640x480"
RTSP_FPS="15"
RTSP_H264_GOP="15" # I-frame interval in frames
RTSP_STREAM_PATH="/live"

# --- End Configuration Section ---

# Get the directory where the script is located (though not strictly needed for config anymore)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default image name (you can change this)
DOCKER_IMAGE_NAME="rtsp-clock-server:latest"

echo "Configuration for Docker (to be passed as environment variables):"
echo "  RTSP_VIEWER_USERNAME: \"$RTSP_VIEWER_USERNAME\""
echo "  RTSP_VIEWER_PASSWORD: [Password is set but not displayed]"
echo "  RTSP_SERVER_IP:       \"$RTSP_SERVER_IP\""
echo "  RTSP_SERVER_PORT:     \"$RTSP_SERVER_PORT\""
echo "  RTSP_VIDEO_CODEC:     \"$RTSP_VIDEO_CODEC\""
echo "  RTSP_VIDEO_RESOLUTION:\"$RTSP_VIDEO_RESOLUTION\""
echo "  RTSP_FPS:             \"$RTSP_FPS\""
echo "  RTSP_H264_GOP:        \"$RTSP_H264_GOP\""
echo "  RTSP_STREAM_PATH:     \"$RTSP_STREAM_PATH\""
echo ""
echo "Attempting to map host port $RTSP_SERVER_PORT to container port $RTSP_SERVER_PORT (RTSP)."
echo ""

# Check if Docker image exists, build if not
echo "DEBUG: Checking for Docker image $DOCKER_IMAGE_NAME..."
if [[ "$(docker images -q $DOCKER_IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image $DOCKER_IMAGE_NAME not found. Building..."
  docker build -t "$DOCKER_IMAGE_NAME" "$SCRIPT_DIR" # Assuming Dockerfile is in SCRIPT_DIR
  if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
  fi
fi

echo ""
echo "Starting RTSP Clock Server in Docker container..."
echo "Stream should be available at: rtsp://<your_host_ip>:$RTSP_SERVER_PORT$RTSP_STREAM_PATH"
if [ -n "$RTSP_VIEWER_USERNAME" ]; then
    echo "Username: $RTSP_VIEWER_USERNAME"
fi
echo ""

# Construct the environment variable flags for Docker
ENV_VARS=""
ENV_VARS="$ENV_VARS -e RTSP_VIEWER_USERNAME=$RTSP_VIEWER_USERNAME"
ENV_VARS="$ENV_VARS -e RTSP_VIEWER_PASSWORD=$RTSP_VIEWER_PASSWORD"
ENV_VARS="$ENV_VARS -e RTSP_SERVER_IP=$RTSP_SERVER_IP"
ENV_VARS="$ENV_VARS -e RTSP_SERVER_PORT=$RTSP_SERVER_PORT"
ENV_VARS="$ENV_VARS -e RTSP_VIDEO_CODEC=$RTSP_VIDEO_CODEC"
ENV_VARS="$ENV_VARS -e RTSP_VIDEO_RESOLUTION=$RTSP_VIDEO_RESOLUTION"
ENV_VARS="$ENV_VARS -e RTSP_FPS=$RTSP_FPS"
ENV_VARS="$ENV_VARS -e RTSP_H264_GOP=$RTSP_H264_GOP"
ENV_VARS="$ENV_VARS -e RTSP_STREAM_PATH=$RTSP_STREAM_PATH"

# Docker run command using the ENV_VARS
# No longer mounts config.json
DOCKER_RUN_CMD="docker run -it --rm --name rtsp-clock-app $ENV_VARS -p $RTSP_SERVER_PORT:$RTSP_SERVER_PORT/tcp -p $RTSP_SERVER_PORT:$RTSP_SERVER_PORT/udp $DOCKER_IMAGE_NAME"

echo "Executing Docker command:"
echo "$DOCKER_RUN_CMD"
echo ""
eval "$DOCKER_RUN_CMD" # Using eval to correctly process the ENV_VARS string with spaces and quotes

echo ""
echo "RTSP Clock Server container stopped."
