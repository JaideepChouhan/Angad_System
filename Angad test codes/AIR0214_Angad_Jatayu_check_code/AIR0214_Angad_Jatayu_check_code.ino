// Jai Shree Ram

// Sensor pins
const int analogPin = A0;       // Single sensor
const int ledPin = 13;          // LED for sensor
const int sampleCount = 20;     // Number of samples for averaging

// Sensor variables
float detectionThresholdMax = 1.0;
float detectionThresholdMin = 1.0;
float ambientNoiseLevel = 0;
bool powerCutDetected = false;

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);

  Serial.println("=== Live Wire Detector (Single Sensor) ===");
  
  // Calibrate sensor
  calibrateSensor();
}

void loop() {
  float currentVoltage = readAverageVoltage(analogPin, sampleCount);
  
  // Check live wire detection
  bool liveWireDetected = (currentVoltage > detectionThresholdMax || currentVoltage < detectionThresholdMin);
  
  digitalWrite(ledPin, liveWireDetected ? HIGH : LOW);
  
  // Print status every second
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 1000) {
    lastPrint = millis();
    
    Serial.print("Time: ");
    Serial.print(millis() / 1000);
    Serial.print("s | Sensor: ");
    Serial.print(currentVoltage, 3);
    Serial.print("V ");
    Serial.print(liveWireDetected ? "⚠️  Fault Detected" : "✅ Normal");
    Serial.println();
  }
  
  delay(100);
}

void calibrateSensor() {
  Serial.println("Calibrating... Please ensure no live wires nearby");
  for (int i = 5; i > 0; i--) {
    Serial.print(String(i) + "...");
    delay(1000);
  }
  Serial.println();

  // Measure ambient noise
  ambientNoiseLevel = readAverageVoltage(analogPin, 125);

  detectionThresholdMax = ambientNoiseLevel + 0.5; // 0.7V above ambient
  detectionThresholdMin = ambientNoiseLevel - 0.5;

  Serial.println("Calibration Results:");
  Serial.print("Ambient: ");
  Serial.print(ambientNoiseLevel, 3);
  Serial.print("V, Threshold: [");
  Serial.print(detectionThresholdMin, 3);
  Serial.print("V - ");
  Serial.print(detectionThresholdMax, 3);
  Serial.println("V]");
  
  Serial.println("Calibration complete!");
  Serial.println("==============================================");
}

float readAverageVoltage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(1);
  }
  return (float)sum / samples * (5.0 / 1023.0);
}
