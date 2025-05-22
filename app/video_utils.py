import cv2
import numpy as np
import datetime

class VideoFrameGenerator:
    def __init__(self, config):
        self.config = config
        try:
            self.width, self.height = map(int, config.get("videoResolution", "640x480").split('x'))
        except ValueError:
            print(f"Warning: Invalid videoResolution format '{config.get('videoResolution')}'. Using 640x480.")
            self.width, self.height = 640, 480

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale_time = self.height / 240  # Scale font with resolution
        self.font_scale_conn = self.height / 320
        self.font_color = (255, 255, 255)  # White
        self.bg_color = (0, 0, 0)  # Black
        self.line_type = 2
        self._connection_count = 0

    def set_connection_count(self, count):
        self._connection_count = count

    def generate_bgr_frame(self):
        frame = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
        conn_str = f"Connected Clients: {self._connection_count}"

        # Calculate text size and position for time
        (tw, th), _ = cv2.getTextSize(time_str, self.font, self.font_scale_time, self.line_type)
        time_x = (self.width - tw) // 2
        time_y = (self.height // 2) - (th // 2) - int(self.height * 0.05) # Slightly above center

        # Calculate text size and position for connection count
        (cw, ch), _ = cv2.getTextSize(conn_str, self.font, self.font_scale_conn, self.line_type)
        conn_x = (self.width - cw) // 2
        conn_y = (self.height // 2) + (ch // 2) + int(self.height * 0.1) # Below center

        cv2.putText(frame, time_str, (time_x, time_y), self.font, self.font_scale_time, self.font_color, self.line_type)
        cv2.putText(frame, conn_str, (conn_x, conn_y), self.font, self.font_scale_conn, self.font_color, self.line_type)
        return frame # BGR format