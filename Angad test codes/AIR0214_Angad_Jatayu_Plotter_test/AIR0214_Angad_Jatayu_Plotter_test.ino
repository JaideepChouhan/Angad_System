// Jai Shree Ram
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ================== Sensor Config ==================
const int analogPin = A0;       // Sensor input
const int sampleCount = 20;     // Samples for averaging

// ================== Detection Variables ==================
float detectionThresholdMax = 1.0;
float detectionThresholdMin = 1.0;
float ambientNoiseLevel = 0;
bool faultDetected = false;

// ===== nRF24L01 Setup =====
#define CE_PIN  2
#define CSN_PIN 3
RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// Timeout for acknowledgment (ms)
const unsigned long ackTimeout = 2000;

void setup() {
  Serial.begin(9600);
  Serial.println("=== Live Wire Detector (Graph + nRF24) ===");

  // nRF24 Init
  if (!radio.begin()) {
    Serial.println("❌ nRF24 init failed");
    while(1);
  }
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();

  // Calibrate sensor
  calibrateSensor();

  // Legends for Serial Plotter
  Serial.println("RealTimeValue, ThresholdMax, ThresholdMin, FaultDetection");
}

void loop() {
  float currentVoltage = readAverageVoltage(analogPin, sampleCount);

  // Detection logic
  bool liveWireDetected = (currentVoltage > detectionThresholdMax || currentVoltage < detectionThresholdMin);

  // Stream values to Serial Plotter (PC)
  Serial.print(currentVoltage, 3);
  Serial.print(" ");
  Serial.print(detectionThresholdMax, 3);
  Serial.print(" ");
  Serial.print(detectionThresholdMin, 3);
  Serial.print(" ");
  Serial.println(liveWireDetected ? 1 : 0);

  // Send messages only on state change
  if (liveWireDetected && !faultDetected) {
    faultDetected = true;
    String msg = "ALERT:head0001:FAULT:" + String(currentVoltage, 3);
    sendMessageToNodeMCU(msg);
  } 
  else if (!liveWireDetected && faultDetected) {
    faultDetected = false;
    String msg = "RECOVERY:head0001:OK:" + String(currentVoltage, 3);
    sendMessageToNodeMCU(msg);
  }

  delay(100);
}

// ================== Send Message ==================
void sendMessageToNodeMCU(String msg) {
  char msgBuf[32];
  msg.toCharArray(msgBuf, sizeof(msgBuf));

  Serial.println("➡️ Sending to NodeMCU: " + msg);
  radio.write(&msgBuf, sizeof(msgBuf));
}

// ================== Calibration ==================
void calibrateSensor() {
  Serial.println("Calibrating... Please ensure no live wires nearby");
  for (int i = 5; i > 0; i--) {
    Serial.print(String(i) + "...");
    delay(1000);
  }
  Serial.println();

  // Ambient noise level
  ambientNoiseLevel = readAverageVoltage(analogPin, 125);

  // Thresholds (±0.5V margin)
  detectionThresholdMax = ambientNoiseLevel + 0.5;
  detectionThresholdMin = ambientNoiseLevel - 0.5;

  // Print results
  Serial.println("Calibration Results:");
  Serial.print("Ambient: ");
  Serial.print(ambientNoiseLevel, 3);
  Serial.print("V, Threshold: [");
  Serial.print(detectionThresholdMin, 3);
  Serial.print("V - ");
  Serial.print(detectionThresholdMax, 3);
  Serial.println("V]");
  Serial.println("==============================================");
}

// ================== Sensor Reading ==================
float readAverageVoltage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(1);
  }
  return (float)sum / samples * (5.0 / 1023.0);
}
