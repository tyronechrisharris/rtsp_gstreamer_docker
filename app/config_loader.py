import json
import os

DEFAULT_CONFIG = {
    "viewerUsername": "", # Empty means no auth
    "viewerPassword": "", # Empty means no auth
    "serverIPAddress": "0.0.0.0", # Listen on all interfaces within Docker
    "serverPort": 8554,
    "videoCodec": "h264", # "mjpeg" or "h264"
    "videoResolution": "640x480",
    "framesPerSecond": 15,
    "h264IFrameInterval": 15, # In frames (GOP size)
    "rtspStreamPath": "/live"
}

CONFIG_FILE_PATH = os.getenv("CONFIG_PATH", "/app/config.json") # Path inside container

def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"WARNING: Configuration file '{CONFIG_FILE_PATH}' not found. Using default configuration.")
        # In a container, we might not want to write a default config,
        # but rather expect it to be mounted.
        # For robustness, we can return defaults or raise an error.
        # Let's return defaults and print a clear warning.
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_from_file = json.load(f)
            # Merge with defaults to ensure all keys are present
            config = DEFAULT_CONFIG.copy()
            config.update(config_from_file)

            # Validate types/values if necessary
            config["serverPort"] = int(config["serverPort"])
            config["framesPerSecond"] = int(config["framesPerSecond"])
            config["h264IFrameInterval"] = int(config["h264IFrameInterval"])
            if not isinstance(config["videoResolution"], str) or 'x' not in config["videoResolution"]:
                print(f"Warning: Invalid videoResolution '{config['videoResolution']}'. Falling back to default.")
                config["videoResolution"] = DEFAULT_CONFIG["videoResolution"]
            return config
    except json.JSONDecodeError:
        print(f"ERROR: Configuration file '{CONFIG_FILE_PATH}' contains invalid JSON. Using default configuration.")
        return DEFAULT_CONFIG
    except Exception as e:
        print(f"ERROR: Could not load config: {e}. Using default configuration.")
        return DEFAULT_CONFIG

if __name__ == '__main__':
    # This part is mainly for host-side testing if needed
    # To create a default config if run directly on host
    if not os.path.exists("config.json"): # Check for local config.json
        print("Creating default 'config.json' in current directory...")
        with open("config.json", 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print("Default 'config.json' created. Mount this into the container at /app/config.json")
    else:
        cfg = load_config() # Test loading
        print("Current Configuration (as loaded):")
        print(json.dumps(cfg, indent=4))