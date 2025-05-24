import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib, GObject

import cv2 
import numpy as np
import signal
import os 

# Updated to use load_config_from_env
from config_loader import load_config_from_env
from video_utils import VideoFrameGenerator

# Global state
connection_count = 0
video_generator = None 
config = None 
loop = None 

def on_need_data(src, length): # src is the appsrc element
    global video_generator
    if video_generator:
        frame_bgr = video_generator.generate_bgr_frame()
        data = frame_bgr.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        
        # Ensure the appsrc is still valid and not flushing
        if src.get_state(0)[1] == Gst.State.PLAYING: # Check if appsrc is in PLAYING state
            retval = src.emit("push-buffer", buf)
            if retval != Gst.FlowReturn.OK:
                # Avoid printing excessively if it's always flushing for a disconnected client
                if retval != Gst.FlowReturn.FLUSHING:
                     print(f"Error pushing buffer via appsrc signal: {retval}")
                return False # Stop pushing if not OK
        else:
            # print("Appsrc not in playing state, skipping push-buffer") # Optional debug
            return False # Stop if not playing
            
    return True # Continue emitting need-data if all good

def client_connected(server, client): # client is GstRtspServer.RTSPClient
    global connection_count, video_generator
    connection_count += 1
    if video_generator:
        video_generator.set_connection_count(connection_count)
    
    # Use a generic client identifier for logging if session ID is problematic
    client_id_for_log = id(client) 
    
    print(f"Client connected (Object ID: {client_id_for_log}). Total clients: {connection_count}")
    client.connect("closed", client_disconnected_callback, server)

def client_disconnected_callback(client, server_obj_ref_unused): # client is GstRtspServer.RTSPClient
    global connection_count, video_generator
    connection_count = max(0, connection_count - 1)
    if video_generator:
        video_generator.set_connection_count(connection_count)
    
    client_id_for_log = id(client)
        
    print(f"Client disconnected (Object ID: {client_id_for_log}). Total clients: {connection_count}")

class ClockServerMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.set_shared(True)
        self.set_latency(0) 
        self.set_transport_mode(GstRtspServer.RTSPTransportMode.PLAY)

    def do_create_element(self, url):
        global config # config is now loaded from env by main()
        width, height = map(int, config.get("videoResolution").split('x'))
        fps = config.get("framesPerSecond")
        codec = config.get("videoCodec").lower() # .lower() already handled in config_loader
        h264_gop = config.get("h264IFrameInterval")
        
        caps_str = f"video/x-raw,format=BGR,width={width},height={height},framerate={fps}/1"

        if codec == "h264":
            encoder_str = f"videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast tune=zerolatency bitrate=1024 key-int-max={h264_gop}"
            payloader_str = "rtph264pay name=pay0 pt=96"
        elif codec == "mjpeg":
            encoder_str = "videoconvert ! jpegenc quality=80" 
            payloader_str = "rtpjpegpay name=pay0 pt=26"
        else:
            # This case should ideally be caught by config_loader validation
            print(f"ERROR: Unsupported video codec in do_create_element: {codec}")
            return None

        launch_string = (
            f"appsrc name=clocksyncsrc format=time is-live=true block=true do-timestamp=true caps={caps_str} ! "
            f"queue max-size-buffers=5 leaky=downstream ! " 
            f"{encoder_str} ! "
            f"queue max-size-buffers=5 leaky=downstream ! " 
            f"{payloader_str}"
        )
        print(f"Using GStreamer launch string: {launch_string}")
        try:
            element = Gst.parse_launch(launch_string)
            return element
        except GLib.Error as e:
            print(f"Error parsing GStreamer launch string: {e}")
            return None

    def do_media_configure(self, media):
        pipeline = media.get_element()
        if not pipeline:
            print("ERROR: Failed to get pipeline element in media_configure")
            return False 
        appsrc = pipeline.get_by_name("clocksyncsrc")
        if appsrc:
            appsrc.connect('need-data', on_need_data)
        else:
            print("ERROR: Could not find appsrc element in pipeline for media_configure.")
            return False 
        return True

def main():
    global config, video_generator, loop 
    
    Gst.init(None) # Initialize GStreamer

    # Load configuration from environment variables
    config = load_config_from_env()
    
    # Initialize VideoFrameGenerator with the loaded configuration
    video_generator = VideoFrameGenerator(config) 
    video_generator.set_connection_count(connection_count) # Set initial count

    loop = GLib.MainLoop()

    def signal_handler(sig, frame):
        print("\\nCaught signal, shutting down gracefully...")
        if loop and loop.is_running():
            loop.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = GstRtspServer.RTSPServer() 
    server.set_address(config.get("serverIPAddress"))
    server.set_service(str(config.get("serverPort"))) 

    mounts = server.get_mount_points()
    if not mounts:
        print("ERROR: Could not get mount points")
        return

    factory = ClockServerMediaFactory()
    mount_path = config.get("rtspStreamPath")
    mounts.add_factory(mount_path, factory)

    auth = None
    # Check for viewerUsername from the config dictionary
    if config.get("viewerUsername") and config.get("viewerPassword"):
        auth = GstRtspServer.RTSPAuth()
        auth.add_basic_watch(config.get("viewerUsername"), config.get("viewerPassword"))
        server.set_auth(auth)
        print(f"Authentication enabled for user: {config.get('viewerUsername')}")

    server.connect("client-connected", client_connected)
    
    server_id = server.attach(None) 
    if server_id == 0:
        print("ERROR: Failed to attach RTSP server to main context.")
        return

    print(f"RTSP Server started on rtsp://{config.get('serverIPAddress')}:{config.get('serverPort')}{config.get('rtspStreamPath')}")
    if config.get("viewerUsername"): # Check again for the print message
        print(f"Connect with username: {config.get('viewerUsername')}")

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Loop interrupted by user.")
    finally:
        print("Shutting down server...")
        print("Server stopped.")

if __name__ == '__main__':
    main()
