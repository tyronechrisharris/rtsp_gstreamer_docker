@echo off
setlocal

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%config.json"

REM Default image name (you can change this)
set "DOCKER_IMAGE_NAME=rtsp-clock-server:latest"

REM Check if config.json exists
if not exist "%CONFIG_FILE%" (
    echo Error: config.json not found in %SCRIPT_DIR%.
    echo Please create it. You can run "python app\config_loader.py" in the app directory to generate a default one locally.
    exit /b 1
)

REM Attempt to read serverPort from config.json (basic parsing)
set "SERVER_PORT="
for /f "tokens=2 delims=:," %%a in ('findstr /C:"\"serverPort\"" "%CONFIG_FILE%"') do (
    set "TEMP_PORT=%%a"
    set "TEMP_PORT=%TEMP_PORT: =%"
    set "TEMP_PORT=%TEMP_PORT:\"=%"
    if defined TEMP_PORT set "SERVER_PORT=%TEMP_PORT%"
)

if not defined SERVER_PORT (
    echo Warning: Could not reliably parse 'serverPort' from config.json. Defaulting to 8554 for port mapping.
    set "SERVER_PORT=8554"
)
echo Attempting to map host port %SERVER_PORT% to container port %SERVER_PORT% (RTSP).

REM Check if Docker image exists, build if not (optional)
docker image inspect %DOCKER_IMAGE_NAME% >nul 2>nul
if errorlevel 1 (
  echo Docker image %DOCKER_IMAGE_NAME% not found. Building...
  docker build -t %DOCKER_IMAGE_NAME% .
  if errorlevel 1 (
    echo Docker build failed. Exiting.
    exit /b 1
  )
)

REM Attempt to read rtspStreamPath from config.json (basic parsing)
set "RTSP_PATH="
for /f "tokens=2 delims=:," %%a in ('findstr /C:"\"rtspStreamPath\"" "%CONFIG_FILE%"') do (
    set "TEMP_PATH=%%a"
    set "TEMP_PATH=%TEMP_PATH: =%"
    set "TEMP_PATH=%TEMP_PATH:\"=%"
    if defined TEMP_PATH set "RTSP_PATH=%TEMP_PATH%"
)
if not defined RTSP_PATH ( set "RTSP_PATH=/live" )


echo Starting RTSP Clock Server in Docker container...
echo Configuration will be read from: %CONFIG_FILE%
echo Stream should be available at: rtsp://<your_host_ip>:%SERVER_PORT%%RTSP_PATH%

REM Attempt to read username (very basic)
set "USERNAME_LINE="
for /f "delims=" %%L in ('findstr /C:"\"viewerUsername\"" "%CONFIG_FILE%"') do set "USERNAME_LINE=%%L"
if defined USERNAME_LINE (
    for /f "tokens=2 delims=:," %%u in ("%USERNAME_LINE%") do (
        set "USERNAME_VAL=%%u"
        set "USERNAME_VAL=%USERNAME_VAL: =%"
        set "USERNAME_VAL=%USERNAME_VAL:\"=%"
        if defined USERNAME_VAL if not "%USERNAME_VAL%"=="" echo Username: %USERNAME_VAL%
    )
)


REM Run the Docker container
docker run -it --rm ^
    --name rtsp-clock-app ^
    -v "%CONFIG_FILE%":/app/config.json:ro ^
    -p %SERVER_PORT%:%SERVER_PORT%/tcp ^
    -p %SERVER_PORT%:%SERVER_PORT%/udp ^
    %DOCKER_IMAGE_NAME%

echo RTSP Clock Server container stopped.
endlocal
pause