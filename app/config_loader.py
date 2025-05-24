import os
import json

# These defaults will be used if corresponding environment variables are not set.
# The keys used here for defaults match the environment variable names for clarity.
DEFAULT_CONFIG_VALUES = {
    "RTSP_VIEWER_USERNAME": "",
    "RTSP_VIEWER_PASSWORD": "",
    "RTSP_SERVER_IP": "0.0.0.0", # Should remain 0.0.0.0 for Docker
    "RTSP_SERVER_PORT": 8554,
    "RTSP_VIDEO_CODEC": "h264",    # "mjpeg" or "h264"
    "RTSP_VIDEO_RESOLUTION": "640x480",
    "RTSP_FPS": 15,
    "RTSP_H264_GOP": 15,      # I-frame interval in frames
    "RTSP_STREAM_PATH": "/live"
}

def load_config_from_env():
    """
    Loads configuration from environment variables.
    Uses default values if an environment variable is not set or if conversion fails.
    """
    config = {} # This will store the final config keys expected by the application

    # Helper function to get env var or default, with type conversion
    def get_env_or_default(env_var_name, default_value, var_type=str):
        value_str = os.getenv(env_var_name)
        if value_str is None:
            # print(f"DEBUG: Env var '{env_var_name}' not set, using default: {default_value}")
            return default_value
        
        if var_type == int:
            try:
                return int(value_str)
            except ValueError:
                print(f"Warning: Invalid integer value for '{env_var_name}': '{value_str}'. Using default: {default_value}")
                return default_value
        elif var_type == str:
            return value_str
        # Add other types if needed (e.g., float, bool)
        return value_str # Default to string if type not specified

    config["viewerUsername"] = get_env_or_default("RTSP_VIEWER_USERNAME", DEFAULT_CONFIG_VALUES["RTSP_VIEWER_USERNAME"])
    config["viewerPassword"] = get_env_or_default("RTSP_VIEWER_PASSWORD", DEFAULT_CONFIG_VALUES["RTSP_VIEWER_PASSWORD"])
    config["serverIPAddress"] = get_env_or_default("RTSP_SERVER_IP", DEFAULT_CONFIG_VALUES["RTSP_SERVER_IP"])
    config["serverPort"] = get_env_or_default("RTSP_SERVER_PORT", DEFAULT_CONFIG_VALUES["RTSP_SERVER_PORT"], var_type=int)
    config["videoCodec"] = get_env_or_default("RTSP_VIDEO_CODEC", DEFAULT_CONFIG_VALUES["RTSP_VIDEO_CODEC"]).lower()
    config["videoResolution"] = get_env_or_default("RTSP_VIDEO_RESOLUTION", DEFAULT_CONFIG_VALUES["RTSP_VIDEO_RESOLUTION"])
    config["framesPerSecond"] = get_env_or_default("RTSP_FPS", DEFAULT_CONFIG_VALUES["RTSP_FPS"], var_type=int)
    config["h264IFrameInterval"] = get_env_or_default("RTSP_H264_GOP", DEFAULT_CONFIG_VALUES["RTSP_H264_GOP"], var_type=int)
    config["rtspStreamPath"] = get_env_or_default("RTSP_STREAM_PATH", DEFAULT_CONFIG_VALUES["RTSP_STREAM_PATH"])

    # Basic validation for resolution format
    if 'x' not in config["videoResolution"] or len(config["videoResolution"].split('x')) != 2:
        print(f"Warning: Invalid videoResolution format '{config['videoResolution']}'. Using default: {DEFAULT_CONFIG_VALUES['RTSP_VIDEO_RESOLUTION']}")
        config["videoResolution"] = DEFAULT_CONFIG_VALUES["RTSP_VIDEO_RESOLUTION"]
    
    # Ensure codec is one of the supported values
    if config["videoCodec"] not in ["h264", "mjpeg"]:
        print(f"Warning: Unsupported videoCodec '{config['videoCodec']}'. Using default: {DEFAULT_CONFIG_VALUES['RTSP_VIDEO_CODEC']}")
        config["videoCodec"] = DEFAULT_CONFIG_VALUES["RTSP_VIDEO_CODEC"]


    print("Configuration loaded by Python script (from environment variables or defaults):")
    # Using a temporary dict for printing to show the actual env var names if they were used
    # This is just for more informative logging. The `config` dict uses app-internal keys.
    effective_settings_log = {
        "RTSP_VIEWER_USERNAME": config["viewerUsername"],
        "RTSP_VIEWER_PASSWORD": config["viewerPassword"], # Be cautious about logging passwords
        "RTSP_SERVER_IP": config["serverIPAddress"],
        "RTSP_SERVER_PORT": config["serverPort"],
        "RTSP_VIDEO_CODEC": config["videoCodec"],
        "RTSP_VIDEO_RESOLUTION": config["videoResolution"],
        "RTSP_FPS": config["framesPerSecond"],
        "RTSP_H264_GOP": config["h264IFrameInterval"],
        "RTSP_STREAM_PATH": config["rtspStreamPath"]
    }
    print(json.dumps(effective_settings_log, indent=4))
    
    return config

if __name__ == '__main__':
    # This part is for testing config_loader.py directly if needed
    # To test, you would set environment variables in your shell before running this script, e.g.:
    # export RTSP_SERVER_PORT="9554"
    # export RTSP_VIDEO_RESOLUTION="1280x720"
    # python3 app/config_loader.py
    
    print("\n--- Testing config_loader.py ---")
    
    # Simulate some environment variables being set
    os.environ["RTSP_SERVER_PORT"] = "9999"
    os.environ["RTSP_VIDEO_CODEC"] = "MJPEG" # Test case insensitivity and different value
    os.environ["RTSP_VIEWER_USERNAME"] = "test_user_env"
    # RTSP_FPS will use default as it's not set here

    loaded_config = load_config_from_env()
    
    print("\n--- Example of directly accessing loaded config values: ---")
    print(f"Viewer Username: {loaded_config.get('viewerUsername')}")
    print(f"Server Port: {loaded_config.get('serverPort')}")
    print(f"Video Codec: {loaded_config.get('videoCodec')}")
    print(f"FPS (should be default if not set in env): {loaded_config.get('framesPerSecond')}")

    # Clean up test environment variables if they were set by this script
    del os.environ["RTSP_SERVER_PORT"]
    del os.environ["RTSP_VIDEO_CODEC"]
    del os.environ["RTSP_VIEWER_USERNAME"]
