import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib, GObject

import cv2 # For frame to Gst.Buffer conversion if needed, or use numpy directly
import numpy as np
import signal

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
        buf.pts = Gst.CLOCK_TIME_NONE # Let appsrc manage timestamps if it can
        buf.duration = Gst.CLOCK_TIME_NONE
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


class ClockServerMediaFactory(GstRtspServer.MediaFactory):
    def __init__(self):
        GstRtspServer.MediaFactory.__init__(self)
        self.set_shared(True) # Single pipeline for all clients

    def do_create_element(self, url):
        global config, video_generator # Access global config and generator

        width, height = map(int, config.get("videoResolution").split('x'))
        fps = config.get("framesPerSecond")
        codec = config.get("videoCodec").lower()
        h264_gop = config.get("h264IFrameInterval")
        
        # Caps for appsrc: BGR format from OpenCV
        # Note: GStreamer might be faster if OpenCV generates in a format closer to what x264enc prefers (e.g., I420)
        # but videoconvert can handle the BGR -> I420 (or other) conversion.
        caps_str = f"video/x-raw,format=BGR,width={width},height={height},framerate={fps}/1"

        if codec == "h264":
            # key-int-max is GOP size
            encoder_str = f"videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency bitrate=1024 key-int-max={h264_gop}"
            payloader_str = "rtph264pay name=pay0 pt=96"
        elif codec == "mjpeg":
            encoder_str = "videoconvert ! jpegenc quality=80" # Adjust quality as needed
            payloader_str = "rtpjpegpay name=pay0 pt=26"
        else:
            raise ValueError(f"Unsupported video codec: {codec}")

        # Full pipeline string
        # appsrc needs `is-live=true` and `do-timestamp=true` can be useful if not setting PTS manually
        # `block=true` makes appsrc block in push_buffer if queue is full, good for live sources
        # Added queue elements for buffering between threads/elements
        launch_string = (
            f"appsrc name=clocksyncsrc format=time is-live=true block=true caps={caps_str} ! "
            f"queue max-size-buffers=2 leaky=downstream ! " # Add queue after appsrc
            f"{encoder_str} ! "
            f"queue max-size-buffers=2 leaky=downstream ! " # Add queue before payloader
            f"{payloader_str}"
        )
        print(f"Using GStreamer launch string: {launch_string}")
        return Gst.parse_launch(launch_string)

    def do_media_configure(self, media):
        # Get the appsrc element and connect 'need-data'
        pipeline = media.get_element()
        appsrc = pipeline.get_by_name("clocksyncsrc")
        if appsrc:
            appsrc.connect('need-data', on_need_data)
        else:
            print("ERROR: Could not find appsrc element in pipeline for media_configure.")
        # No specific media configure needed for appsrc beyond this for this example


def main():
    global config, video_generator, loop # Allow modification of globals

    GObject.threads_init() # Safe for GStreamer and GLib multi-threading
    Gst.init(None)

    config = load_config()
    video_generator = VideoFrameGenerator(config)
    video_generator.set_connection_count(connection_count) # Initial count

    loop = GLib.MainLoop()

    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nCaught signal, shutting down gracefully...")
        loop.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = GstRtspServer.Server()
    server.set_address(config.get("serverIPAddress"))
    server.set_service(str(config.get("serverPort"))) # Port must be a string

    mounts = server.get_mount_points()
    if not mounts:
        print("ERROR: Could not get mount points")
        return

    factory = ClockServerMediaFactory()
    mount_path = config.get("rtspStreamPath")
    mounts.add_factory(mount_path, factory)

    # Authentication
    auth = None
    if config.get("viewerUsername") and config.get("viewerPassword"):
        auth = GstRtspServer.Auth()
        token = GstRtspServer.Token()
        token.set_string("username", config.get("viewerUsername"))
        token.set_string("password", config.get("viewerPassword"))
        # BasicAuth is simple, DigestAuth is more secure if client supports
        basic_auth = GstRtspServer.AuthBasic() # You could use Digest: GstRtspServer.AuthDigest.new_from_data(...)
        auth.set_basic_credentials_callback(lambda cred, user_data: basic_auth, None) # Simplified
        auth.add_basic_watch(config.get("viewerUsername"), config.get("viewerPassword"))
        server.set_auth(auth)
        print(f"Authentication enabled for user: {config.get('viewerUsername')}")


    # Connect client signals
    server.connect("client-connected", client_connected)
    # Note: client_disconnected is handled by connecting to the 'closed' signal of each client instance.

    server_id = server.attach(None) # Attach to default GLib main context
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
        # GLib.Source.remove(server_id) # Not strictly necessary if loop.quit() is used
        # Cleanup if needed, though GObject usually handles its own destruction.
        print("Server stopped.")

if __name__ == '__main__':
    main()