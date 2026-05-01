import cv2
import mediapipe as mp
import serial
import time

# --- SETUP SERIAL ---
# Establishes a serial connection with the ESP32 microcontroller.
# This is used to send signals to the buzzer.
# Update 'COM3' to the port shown in your Arduino IDE
try:
    arduino = serial.Serial(port='COM3', baudrate=115200, timeout=0.1)
    time.sleep(2) # Wait for the connection to establish
    print("Connected to ESP32")
except Exception as e:
    print(f"Serial Error: {e}. Check if Serial Monitor is open!")
    arduino = None

# --- MEDIAPIPE SETUP ---
# Initializes the MediaPipe Face Mesh model for detecting facial landmarks.
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Indices for Eyes in MediaPipe Mesh
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def get_ear(landmarks, eye_indices):
    """
    Calculates the Eye Aspect Ratio (EAR) for a single eye.
    The EAR is a measure of eye openness.
    """
    def dist(p1, p2):
        """Calculates the euclidean distance between two points."""
        return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5
    # Vertical distances
    v1 = dist(landmarks[eye_indices[1]], landmarks[eye_indices[5]])
    v2 = dist(landmarks[eye_indices[2]], landmarks[eye_indices[4]])
    # Horizontal distance
    h = dist(landmarks[eye_indices[0]], landmarks[eye_indices[3]])
    # Eye Aspect Ratio
    return (v1 + v2) / (2.0 * h)

# --- CONFIGURATION ---
# These values can be tuned to adjust the sensitivity of the drowsiness detection.
EAR_THRESHOLD = 0.21    # The minimum EAR to be considered "awake". Adjust if the alarm triggers too easily or not at all.
CONSEC_FRAMES = 15      # The number of consecutive frames the eyes must be closed for to trigger the alarm.
counter = 0             # A counter for the number of consecutive frames with a low EAR.

# --- WEBCAM SETUP ---
# Initializes the webcam.
cap = cv2.VideoCapture(0)

# --- MAIN LOOP ---
# Continuously captures frames from the webcam, processes them for drowsiness,
# and displays the output.
while cap.isOpened():
    # Reads a frame from the webcam.
    success, frame = cap.read()
    if not success:
        break

    # Flips the frame horizontally for a mirror-like view.
    frame = cv2.flip(frame, 1)
    # Converts the BGR image to RGB for MediaPipe.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Processes the frame with the Face Mesh model.
    results = face_mesh.process(rgb)

    # If a face is detected, calculate the EAR and check for drowsiness.
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark
            # Calculates the average EAR for both eyes.
            ear = (get_ear(landmarks, LEFT_EYE) + get_ear(landmarks, RIGHT_EYE)) / 2.0

            # If the EAR is below the threshold, increment the counter.
            if ear < EAR_THRESHOLD:
                counter += 1
                # If the eyes have been closed for a sufficient number of frames, trigger the alarm.
                if counter >= CONSEC_FRAMES:
                    cv2.putText(frame, "DROWSY!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
                    if arduino: arduino.write(b'1') # Send a signal to the ESP32 to turn on the buzzer.
            else:
                # If the eyes are open, reset the counter and turn off the buzzer.
                counter = 0
                if arduino: arduino.write(b'0')

    # Displays the frame in a window.
    cv2.imshow('System Monitor', frame)
    # Breaks the loop if the ESC key is pressed.
    if cv2.waitKey(1) & 0xFF == 27:
        break

# --- CLEANUP ---
# Releases the webcam and closes all OpenCV windows.
cap.release()
cv2.destroyAllWindows()