import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib, GObject

import cv2 # For frame to Gst.Buffer conversion if needed, or use numpy directly
import numpy as np
import signal
import os # For checking if running in Docker, if needed for other logic

from config_loader import load_config
from video_utils import VideoFrameGenerator

# Global state (consider encapsulating in a class if it grows)
connection_count = 0
video_generator = None # To be initialized after config
config = None # To be initialized
loop = None # GLib MainLoop

def on_need_data(src, length):
    global video_generator
    if video_generator:
        frame_bgr = video_generator.generate_bgr_frame()
        # GStreamer expects RGB or other formats, BGR needs conversion if pipeline assumes RGB
        # Or, ensure appsrc caps specify BGR if downstream elements can handle it
        # For x264enc, it typically wants I420 or NV12. videoconvert will handle this.
        data = frame_bgr.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        # Timestamps: It's often better to let GStreamer handle timestamps if possible,
        # especially with appsrc's do-timestamp=true.
        # If you set PTS manually, you need to manage it carefully.
        # buf.pts = Gst.CLOCK_TIME_NONE # Let appsrc manage timestamps
        # buf.duration = Gst.CLOCK_TIME_NONE # Or calculate based on FPS
        retval = src.push_buffer(buf)
        if retval != Gst.FlowReturn.OK:
            print(f"Error pushing buffer to appsrc: {retval}")
            return False # Stop pushing
    return True # Continue pushing

def client_connected(server, client):
    global connection_count, video_generator
    connection_count += 1
    if video_generator:
        video_generator.set_connection_count(connection_count)
    print(f"Client connected (ID: {client.get_session_id()}). Total clients: {connection_count}")
    # You can connect to client signals here if needed, e.g., 'closed'
    client.connect("closed", client_disconnected_callback, server) # Pass server or other context if needed

def client_disconnected_callback(client, server_obj_ref_unused): # server_obj_ref is just to match signal signature
    global connection_count, video_generator
    connection_count = max(0, connection_count - 1) # Ensure it doesn't go below zero
    if video_generator:
        video_generator.set_connection_count(connection_count)
    print(f"Client disconnected (ID: {client.get_session_id()}). Total clients: {connection_count}")


# Corrected base class from MediaFactory to RTSPMediaFactory
class ClockServerMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        # Corrected __init__ call
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.set_shared(True) # Single pipeline for all clients
        self.set_latency(0) # Optional: try to reduce latency
        self.set_transport_mode(GstRtspServer.RTSPTransportMode.PLAY) # Ensure it's for PLAY

    def do_create_element(self, url):
        global config, video_generator # Access global config and generator

        width, height = map(int, config.get("videoResolution").split('x'))
        fps = config.get("framesPerSecond")
        codec = config.get("videoCodec").lower()
        h264_gop = config.get("h264IFrameInterval")
        
        caps_str = f"video/x-raw,format=BGR,width={width},height={height},framerate={fps}/1"

        if codec == "h264":
            encoder_str = f"videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast tune=zerolatency bitrate=1024 key-int-max={h264_gop}"
            payloader_str = "rtph264pay name=pay0 pt=96"
        elif codec == "mjpeg":
            encoder_str = "videoconvert ! jpegenc quality=80" 
            payloader_str = "rtpjpegpay name=pay0 pt=26"
        else:
            print(f"ERROR: Unsupported video codec: {codec}")
            return None # Return None on error

        launch_string = (
            f"appsrc name=clocksyncsrc format=time is-live=true block=true do-timestamp=true caps={caps_str} ! "
            f"queue max-size-buffers=3 leaky=downstream ! " 
            f"{encoder_str} ! "
            f"queue max-size-buffers=3 leaky=downstream ! " 
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
        appsrc = pipeline.get_by_name("clocksyncsrc")
        if appsrc:
            # Set stream type to seekable if needed, though for live it's usually not.
            # appsrc.set_property("stream-type", 0) # 0 for GstAppStreamType.STREAM (continuous)
            # appsrc.set_property("max-bytes", 0) # No limit
            # appsrc.set_property("min-latency", 0)
            appsrc.connect('need-data', on_need_data)
            # appsrc.connect('enough-data', lambda src: print("Appsrc has enough data")) # Optional debug
            # appsrc.connect('seek-data', lambda src, offset: print(f"Appsrc seek data to {offset}")) # Optional debug
        else:
            print("ERROR: Could not find appsrc element in pipeline for media_configure.")
        # No specific media configure needed for appsrc beyond this for this example
        return True # Must return True on success


def main():
    global config, video_generator, loop 

    # Check if GObject threads are already initialized, which might be the case in some environments
    if not GLib.threads_check():
        GObject.threads_init() 
    
    Gst.init(None)

    config = load_config()
    video_generator = VideoFrameGenerator(config)
    video_generator.set_connection_count(connection_count) 

    loop = GLib.MainLoop()

    def signal_handler(sig, frame):
        print("\nCaught signal, shutting down gracefully...")
        loop.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = GstRtspServer.Server()
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
    if config.get("viewerUsername") and config.get("viewerPassword"):
        auth = GstRtspServer.Auth()
        # Using a simple callback for Basic authentication
        def basic_auth_check(credentials, user_data):
            # This function will be called by GstRtspServer.Auth
            # It needs to return a GstRtspServer.AuthBasic object if credentials are valid
            # or None if invalid.
            # For simplicity, we're pre-populating the token and letting GstRtspServer.Auth manage it.
            # This callback is more for dynamic credential checking from a database, etc.
            # The add_basic_watch method is simpler for static credentials.
            return GstRtspServer.AuthBasic() # This is a placeholder, add_basic_watch is used

        # This is a more direct way for static credentials with Basic Auth
        # Create a token with the credentials
        token = GstRtspServer.RTSPToken() # Use RTSPToken
        token.set_string("media.factory.role", "user") # Example role
        # No direct set_string for username/password on token for basic auth check this way
        
        # The add_basic_watch method is simpler for static credentials
        auth.add_basic_watch(config.get("viewerUsername"), config.get("viewerPassword"))
        server.set_auth(auth)
        print(f"Authentication enabled for user: {config.get('viewerUsername')}")


    server.connect("client-connected", client_connected)
    
    server_id = server.attach(None) 
    if server_id == 0:
        print("ERROR: Failed to attach RTSP server to main context.")
        return

    print(f"RTSP Server started on rtsp://{config.get('serverIPAddress')}:{config.get('serverPort')}{mount_path}")
    if config.get("viewerUsername"):
        print(f"Connect with username: {config.get('viewerUsername')}")

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Loop interrupted by user.")
    finally:
        print("Shutting down server...")
        # server.detach() # Detach from main context if server_id > 0
        print("Server stopped.")

if __name__ == '__main__':
    main()
