@echo off
setlocal

REM # --- Configuration Section ---
REM # Edit these values to configure your RTSP server
REM # These will be passed as environment variables to the Docker container.

set RTSP_VIEWER_USERNAME=
set RTSP_VIEWER_PASSWORD=
REM # RTSP_SERVER_IP should generally be 0.0.0.0 for Docker to listen on all interfaces
set RTSP_SERVER_IP=0.0.0.0
set RTSP_SERVER_PORT=8554
set RTSP_VIDEO_CODEC=h264
set RTSP_VIDEO_RESOLUTION=640x480
set RTSP_FPS=15
set RTSP_H264_GOP=15
set RTSP_STREAM_PATH=/live

REM # --- End Configuration Section ---

REM Get the directory where the script is located (though not strictly needed for config anymore)
set "SCRIPT_DIR=%~dp0"

REM Default image name (you can change this)
set "DOCKER_IMAGE_NAME=rtsp-clock-server:latest"

echo Configuration for Docker (to be passed as environment variables):
echo   RTSP_VIEWER_USERNAME: "%RTSP_VIEWER_USERNAME%"
echo   RTSP_VIEWER_PASSWORD: [Password is set but not displayed]
echo   RTSP_SERVER_IP:       "%RTSP_SERVER_IP%"
echo   RTSP_SERVER_PORT:     "%RTSP_SERVER_PORT%"
echo   RTSP_VIDEO_CODEC:     "%RTSP_VIDEO_CODEC%"
echo   RTSP_VIDEO_RESOLUTION:"%RTSP_VIDEO_RESOLUTION%"
echo   RTSP_FPS:             "%RTSP_FPS%"
echo   RTSP_H264_GOP:        "%RTSP_H264_GOP%"
echo   RTSP_STREAM_PATH:     "%RTSP_STREAM_PATH%"
echo.
echo Attempting to map host port %RTSP_SERVER_PORT% to container port %RTSP_SERVER_PORT% (RTSP).
echo.

REM Check if Docker image exists, build if not
echo DEBUG: Checking for Docker image %DOCKER_IMAGE_NAME%...
docker image inspect %DOCKER_IMAGE_NAME% >nul 2>nul
if errorlevel 1 (
  echo Docker image %DOCKER_IMAGE_NAME% not found. Building...
  docker build -t %DOCKER_IMAGE_NAME% .
  if errorlevel 1 (
    echo Docker build failed. Exiting.
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
REM No longer mounts config.json
set DOCKER_RUN_CMD=docker run -it --rm --name rtsp-clock-app %ENV_VARS% -p %RTSP_SERVER_PORT%:%RTSP_SERVER_PORT%/tcp -p %RTSP_SERVER_PORT%:%RTSP_SERVER_PORT%/udp %DOCKER_IMAGE_NAME%

echo Executing Docker command:
echo %DOCKER_RUN_CMD%
echo.
%DOCKER_RUN_CMD%

echo.
echo RTSP Clock Server container stopped.
endlocal
pause
