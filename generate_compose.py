services = []
for i, port in enumerate(range(8551, 8601), start=1):
    services.append(f"""
  cam{i}:
    image: rtsp_gstreamer_docker
    environment:
      RTSP_PORT: 8554
      FPS: 5
      WIDTH: 640
      HEIGHT: 480
    ports:
      - "{port}:8554"
""")

print("version: '3.9'\nservices:")
print("".join(services))
