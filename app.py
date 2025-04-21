
from flask import Flask, render_template, Response, request, jsonify  # For creating the web server
from flask_cors import CORS  # To allow web frontend to talk to backend
import cv2  # To work with video and webcam
import threading  # To run camera reading in the background
from ultralytics import YOLO  # To use the YOLO model for detecting vehicles

# Create the web app
app = Flask(__name__)
CORS(app)  # Allow communication from other places like a frontend app

# Load the YOLO model (yolov8n.pt is a lightweight version of the model)
model = YOLO("yolov8n.pt")

# Define global variables used by the app
camera = None  # To store the video feed (webcam or file)
output_frame = None  # The last video frame captured
lock = threading.Lock()  # Used to safely update frames across threads
vehicle_count = 0  # This will store the number of vehicles detected
running = False  # Keeps track of whether the camera is on

# This function detects vehicles in a single frame of video
def detect_vehicles(frame):
    global vehicle_count

    # Run the YOLO model on the frame
    results = model(frame)[0]

    # YOLO detects many things (people, animals, etc.) — we want only vehicles:
    # Class IDs for vehicles: 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
    vehicle_classes = [2, 3, 5, 7]

    # Count how many detected objects are vehicles
    vehicle_count = sum(1 for r in results.boxes.cls if int(r) in vehicle_classes)

    # Draw boxes around the detected objects and return the image
    annotated_frame = results.plot()
    return annotated_frame

# This function continuously captures video frames while the camera is running
def generate_frames():
    global camera, output_frame, running

    while running:
        success, frame = camera.read()  # Capture a single frame
        if not success:
            break  # If there's an error reading from the camera, stop

        # Detect vehicles in the frame
        frame = detect_vehicles(frame)

        # Convert the frame to a format that can be sent to the web browser
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Store the current frame for safe access by other parts of the program
        with lock:
            output_frame = frame

        # Send the frame to the browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# This is the route the frontend calls to start showing the video
@app.route('/video_feed')
def video_feed():
    global camera, running

    # Get the source of the video: either 'webcam' or a video file
    source = request.args.get('source', 'video')

    # If the camera is already running, just start sending frames
    if running:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    # Open the webcam if selected, otherwise open a sample video file
    if source == 'webcam':
        camera = cv2.VideoCapture(0)  # 0 = default webcam
    else:
        camera = cv2.VideoCapture('sample_traffic_video.mp4')

    # Start running
    running = True

    # Start sending frames to the frontend
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# This is the route to stop the camera feed
@app.route('/stop_webcam', methods=['POST'])
def stop_webcam():
    global camera, running
    running = False  # Turn off the camera

    # Release the webcam if it's open
    if camera is not None:
        camera.release()

    # Let the frontend know the camera has stopped
    return jsonify({'status': 'Webcam stopped'})

# This route returns the current number of vehicles detected
@app.route('/vehicle_count')
def get_vehicle_count():
    return jsonify({'count': vehicle_count})

# This tells Python to run the web app when the script is executed
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Makes the app accessible locally
