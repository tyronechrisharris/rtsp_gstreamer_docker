@echo off
setlocal

REM # --- Configuration Section ---
REM # This script is pre-configured to run the server on port 555 with the H.264 codec.
REM # Other default values are used.

set RTSP_VIEWER_USERNAME=
set RTSP_VIEWER_PASSWORD=
set RTSP_SERVER_IP=0.0.0.0
set RTSP_SERVER_PORT=555
set RTSP_VIDEO_CODEC=h264
set RTSP_VIDEO_RESOLUTION=640x480
set RTSP_FPS=15
set RTSP_H264_GOP=15
set RTSP_STREAM_PATH=/live

REM # --- End Configuration Section ---

REM Set the public Docker Hub image name
set "DOCKER_IMAGE_NAME=harristc825/rtsp-clock-server:latest"

echo Configuration for this specific launch:
echo   RTSP_SERVER_PORT:     "%RTSP_SERVER_PORT%"
echo   RTSP_VIDEO_CODEC:     "%RTSP_VIDEO_CODEC%"
echo   (Other settings are using defaults from the image)
echo.
echo Attempting to map host port %RTSP_SERVER_PORT% to container port %RTSP_SERVER_PORT% (RTSP).
echo.

REM Check if the Docker image is available locally, if not, pull it.
echo DEBUG: Checking for Docker image %DOCKER_IMAGE_NAME%...
docker image inspect %DOCKER_IMAGE_NAME% >nul 2>nul
if errorlevel 1 (
  echo Docker image %DOCKER_IMAGE_NAME% not found locally. Attempting to pull from Docker Hub...
  docker pull %DOCKER_IMAGE_NAME%
  if errorlevel 1 (
    echo Docker pull failed. Please ensure the image name is correct and you are logged in.
    pause
    exit /b 1
  )
)

echo.
echo Starting RTSP Clock Server in Docker container...
echo Stream should be available at: rtsp://<your_host_ip>:%RTSP_SERVER_PORT%%RTSP_STREAM_PATH%
if defined RTSP_VIEWER_USERNAME if not "%RTSP_VIEWER_USERNAME%"=="" echo Username: %RTSP_VIEWER_USERNAME%
echo.

REM Construct the environment variable flags for Docker
set ENV_VARS=^
    -e "RTSP_VIEWER_USERNAME=%RTSP_VIEWER_USERNAME%" ^
    -e "RTSP_VIEWER_PASSWORD=%RTSP_VIEWER_PASSWORD%" ^
    -e "RTSP_SERVER_IP=%RTSP_SERVER_IP%" ^
    -e "RTSP_SERVER_PORT=%RTSP_SERVER_PORT%" ^
    -e "RTSP_VIDEO_CODEC=%RTSP_VIDEO_CODEC%" ^
    -e "RTSP_VIDEO_RESOLUTION=%RTSP_VIDEO_RESOLUTION%" ^
    -e "RTSP_FPS=%RTSP_FPS%" ^
    -e "RTSP_H264_GOP=%RTSP_H264_GOP%" ^
    -e "RTSP_STREAM_PATH=%RTSP_STREAM_PATH%"

REM Docker run command using the ENV_VARS
REM Giving it a unique container name to avoid conflicts
set DOCKER_RUN_CMD=docker run -it --rm --name rtsp-h264-555-stream %ENV_VARS% -p %RTSP_SERVER_PORT%:%RTSP_SERVER_PORT%/tcp -p %RTSP_SERVER_PORT%:%RTSP_SERVER_PORT%/udp %DOCKER_IMAGE_NAME%

echo Executing Docker command:
echo %DOCKER_RUN_CMD%
echo.
%DOCKER_RUN_CMD%

echo.
echo RTSP Clock Server container stopped.
endlocal
pause
