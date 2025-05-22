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

def on_need_data(src, length): # src is the appsrc element
    global video_generator
    if video_generator:
        frame_bgr = video_generator.generate_bgr_frame()
        data = frame_bgr.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        # Emit the "push-buffer" signal on the appsrc element
        retval = src.emit("push-buffer", buf)
        if retval != Gst.FlowReturn.OK:
            print(f"Error pushing buffer via appsrc signal: {retval}")
            # Consider also returning Gst.FlowReturn.ERROR or similar from need-data
            # For now, returning False to stop the emission for this cycle
            return False 
    return True # Continue pushing / emitting need-data

def client_connected(server, client): # client is GstRtspServer.RTSPClient
    global connection_count, video_generator
    connection_count += 1
    if video_generator:
        video_generator.set_connection_count(connection_count)
    
    # Get session and then session ID
    session = client.get_session()
    session_id = "N/A"
    if session:
        session_id = session.get_id()
    
    print(f"Client connected (Session ID: {session_id}). Total clients: {connection_count}")
    client.connect("closed", client_disconnected_callback, server)

def client_disconnected_callback(client, server_obj_ref_unused): # client is GstRtspServer.RTSPClient
    global connection_count, video_generator
    connection_count = max(0, connection_count - 1)
    if video_generator:
        video_generator.set_connection_count(connection_count)
    
    session = client.get_session()
    session_id = "N/A"
    if session:
        session_id = session.get_id()
        
    print(f"Client disconnected (Session ID: {session_id}). Total clients: {connection_count}")

class ClockServerMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.set_shared(True)
        self.set_latency(0)
        self.set_transport_mode(GstRtspServer.RTSPTransportMode.PLAY)

    def do_create_element(self, url):
        global config
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
            return None

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
            appsrc.connect('need-data', on_need_data)
        else:
            print("ERROR: Could not find appsrc element in pipeline for media_configure.")
        return True

def main():
    global config, video_generator, loop 
    
    # GObject.threads_init() is deprecated and no longer needed.
    Gst.init(None)

    config = load_config()
    video_generator = VideoFrameGenerator(config)
    video_generator.set_connection_count(connection_count) 

    loop = GLib.MainLoop()

    def signal_handler(sig, frame):
        print("\nCaught signal, shutting down gracefully...")
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

    print(f"RTSP Server started on rtsp://{config.get('serverIPAddress')}:{config.get('serverPort')}{mount_path}")
    if config.get("viewerUsername"):
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
