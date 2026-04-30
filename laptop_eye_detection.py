import cv2
import mediapipe as mp
import serial
import time

# --- SETUP SERIAL ---
# Update 'COM3' to the port shown in your Arduino IDE
try:
    arduino = serial.Serial(port='COM3', baudrate=115200, timeout=0.1)
    time.sleep(2) 
    print("Connected to ESP32")
except Exception as e:
    print(f"Serial Error: {e}. Check if Serial Monitor is open!")
    arduino = None

# --- MEDIAPIPE SETUP ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Indices for Eyes in MediaPipe Mesh
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def get_ear(landmarks, eye_indices):
    def dist(p1, p2):
        return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5
    v1 = dist(landmarks[eye_indices[1]], landmarks[eye_indices[5]])
    v2 = dist(landmarks[eye_indices[2]], landmarks[eye_indices[4]])
    h = dist(landmarks[eye_indices[0]], landmarks[eye_indices[3]])
    return (v1 + v2) / (2.0 * h)

# --- CONFIGURATION ---
EAR_THRESHOLD = 0.21    # Adjust if buzzer triggers too early/late
CONSEC_FRAMES = 15      # Frames eyes must be closed to trigger
counter = 0

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark
            ear = (get_ear(landmarks, LEFT_EYE) + get_ear(landmarks, RIGHT_EYE)) / 2.0

            if ear < EAR_THRESHOLD:
                counter += 1
                if counter >= CONSEC_FRAMES:
                    cv2.putText(frame, "DROWSY!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
                    if arduino: arduino.write(b'1')
            else:
                counter = 0
                if arduino: arduino.write(b'0')

    cv2.imshow('System Monitor', frame)
    if cv2.waitKey(1) & 0xFF == 27: break # Press ESC to quit

cap.release()
cv2.destroyAllWindows()