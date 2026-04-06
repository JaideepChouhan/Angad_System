#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// Sensor pins
const int analogPin = A0;
const int ledPin = 13;
const int sampleCount = 20;

// nRF24L01 setup
RF24 radio(2, 3);  // CE, CSN pins
const byte addresses[][6] = {"head1", "devc1", "devc2", "devc3", "devc4"};

const String deviceName = "device0001";

// Power cut detection variables
float detectionThresholdMax = 3.0;  // Upper threshold for power cut
float detectionThresholdMin = 1.0;  // Lower threshold for power cut  
float ambientNoiseLevel = 0;
bool isCalibrated = false;
bool powerCutDetected = false;

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  pinMode(analogPin, INPUT);
  
  if (!radio.begin()) {
    Serial.println("NRF24 hardware not responding!");
    while (1);
  }
  
  radio.openReadingPipe(1, addresses[1]);  // Receive on device0001 pipe
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();
  
  Serial.println("=== Middle Device " + deviceName + " - Sensor Monitor ===");
  
  // Calibrate sensor
  calibrateSensor();
}

void loop() {
  if (!isCalibrated) return;
  
  float currentVoltage = readAverageVoltage(analogPin, sampleCount);
  
  // Power cut detection logic using min/max thresholds
  bool currentPowerCut = (currentVoltage > detectionThresholdMax || currentVoltage < detectionThresholdMin);
  
  digitalWrite(ledPin, currentPowerCut ? HIGH : LOW);
  
  // Power cut status change detection
  if (currentPowerCut != powerCutDetected) {
    powerCutDetected = currentPowerCut;
    
    if (powerCutDetected) {
      Serial.println("🚨 ⚠️ POWER CUT DETECTED! (Alert not sent)");
    } else {
      Serial.println("✅ POWER RESTORED (Notification not sent)");
    }
  }
  
  // Display sensor status every second
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 1000) {
    lastPrint = millis();
    
    Serial.print("⏰ Time: ");
    Serial.print(millis() / 1000);
    Serial.print("s");
    
    // Sensor data
    Serial.print(" | 📊 Sensor: ");
    Serial.print(currentVoltage, 3);
    Serial.print("V ");
    Serial.print(currentPowerCut ? "🚨 POWER CUT" : "✅ NORMAL");
    
    // Threshold info
    Serial.print(" | 📈 Thresholds: [");
    Serial.print(detectionThresholdMin, 2);
    Serial.print("V - ");
    Serial.print(detectionThresholdMax, 2);
    Serial.print("V]");
    
    // Raw ADC value
    Serial.print(" | 🔢 Raw ADC: ");
    Serial.print(analogRead(analogPin));
    
    Serial.println();
  }
  
  // Handle incoming messages (for monitoring only)
  if (radio.available()) {
    char text[64] = "";
    radio.read(&text, sizeof(text));
    Serial.println("📡 Received message: " + String(text));
  }
  
  delay(100);
}

void calibrateSensor() {
  Serial.println("🔧 Calibrating sensor... Ensure normal power conditions");
  
  // Countdown
  for (int i = 5; i > 0; i--) {
    Serial.print(String(i) + "...");
    delay(1000);
  }
  Serial.println();
  
  // Measure ambient/normal power level
  ambientNoiseLevel = readAverageVoltage(analogPin, 100);
  
  // Set thresholds for power cut detection
  detectionThresholdMax = ambientNoiseLevel + 0.5;  // 0.5V above normal
  detectionThresholdMin = ambientNoiseLevel - 0.5;  // 0.5V below normal
  
  Serial.println("✅ Calibration Results:");
  Serial.print("   Normal Power Level: ");
  Serial.print(ambientNoiseLevel, 3);
  Serial.println("V");
  Serial.print("   Detection Range: [");
  Serial.print(detectionThresholdMin, 3);
  Serial.print("V - ");
  Serial.print(detectionThresholdMax, 3);
  Serial.println("V]");
  
  Serial.println("🎯 Calibration complete! Starting monitoring...");
  isCalibrated = true;
}

float readAverageVoltage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return (float)sum / samples * (5.0 / 1023.0);
}