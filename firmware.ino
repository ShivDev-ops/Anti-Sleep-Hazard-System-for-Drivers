/*
  Integrated Drowsiness & Air Quality Monitor
  Buzzer: Pin D13 (GPIO 13)
  MQ-135: Pin D34 (GPIO 34)
*/

const int mq135Pin = 34;   
const int buzzerPin = 13;  

// Frequency settings from your successful experiment
const int freq = 2000;     // The "loud" frequency
const int resolution = 8;  // 8-bit resolution (0-255)
const int gasThreshold = 1800; // Adjust based on your room's baseline

void setup() {
  Serial.begin(115200);
  pinMode(mq135Pin, INPUT);
  
  // Using the specific ESP32 v3.0+ PWM attachment
  ledcAttach(buzzerPin, freq, resolution);
}

void loop() {
  int gasValue = analogRead(mq135Pin);
  bool pythonAlert = false;

  // Check for the '1' signal from Python MediaPipe script
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      pythonAlert = true;
    }
  }

  // Logic to trigger the loud buzzer
  if (pythonAlert || gasValue > gasThreshold) {
    // Force frequency to 2000Hz and Duty Cycle to 128 (50%)
    // This matches the experiment that worked for you.
    ledcWriteTone(buzzerPin, 2000); 
    ledcWrite(buzzerPin, 128); 
  } else {
    // Complete silence when safe
    ledcWrite(buzzerPin, 0); 
  }

  // Small delay to prevent serial buffer overflow
  delay(50); 
}