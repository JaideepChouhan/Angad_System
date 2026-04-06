#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// UART with ESP8266
#define ESP Serial

// Sensor pins
const int analogPin = A0;
const int ledPin = 13;
const int calibrationTime = 5000;
const int sampleCount = 20;

// nRF24L01 setup
RF24 radio(2, 3); // CE, CSN
const byte addresses[][6] = {"1Node", "2Node"};

// Variables
float detectionThresholdMax = 1.0;
float detectionThresholdMin = 1.0;
float ambientNoiseLevel = 0;
bool powerCutDetected = false;
unsigned long lastTransmissionTime = 0;
const unsigned long transmissionInterval = 2000;
bool headConnected = false;
unsigned long connectionCheckTime = 0;
const unsigned long connectionCheckInterval = 3000;

void setup() {
  Serial.begin(9600);   // Debug
  ESP.begin(115200);    // Communication with ESP8266
  pinMode(ledPin, OUTPUT);

  if (!radio.begin()) {
    Serial.println("NRF24 not responding!");
    while (1);
  }

  radio.openWritingPipe(addresses[0]); // Head sends to nodes
  radio.openReadingPipe(1, addresses[1]); // Head listens from nodes
  radio.setPALevel(RF24_PA_LOW);
  radio.setRetries(3, 5);
  radio.startListening();

  Serial.println("=== Head Node Started ===");

  // Calibrate head sensor
  calibrateSensor();
}

void loop() {
  float currentVoltage = readAverageVoltage(analogPin, sampleCount);
  bool liveWireDetected = (currentVoltage > detectionThresholdMax || currentVoltage < detectionThresholdMin);
  digitalWrite(ledPin, liveWireDetected ? HIGH : LOW);

  // Check head's own fault
  bool currentPowerCut = liveWireDetected;
  if (currentPowerCut != powerCutDetected || (currentPowerCut && millis() - lastTransmissionTime > transmissionInterval)) {
    powerCutDetected = currentPowerCut;
    lastTransmissionTime = millis();

    if (powerCutDetected) {
      Serial.println("⚠️ Head detected POWER CUT");
      forwardToServer("HEAD", "POWER_CUT", currentVoltage);
    } else {
      Serial.println("✅ Head POWER RESTORED");
      forwardToServer("HEAD", "NORMAL", currentVoltage);
    }
  }

  // Listen for messages from nodes
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    String message = String(text);
    Serial.print("📩 From Node: ");
    Serial.println(message);

    // Example node sends: "NODE1:POWER_CUT"
    int sep = message.indexOf(':');
    if (sep > 0) {
      String device = message.substring(0, sep);
      String status = message.substring(sep + 1);
      forwardToServer(device, status, currentVoltage);
    }
  }

  delay(100);
}

// ========== Helper Functions ==========

void calibrateSensor() {
  Serial.println("Calibrating HEAD sensor...");
  for (int i = 5; i > 0; i--) {
    Serial.print(i); Serial.print("...");
    delay(1000);
  }
  Serial.println();

  ambientNoiseLevel = readAverageVoltage(analogPin, 125);
  detectionThresholdMax = ambientNoiseLevel + 0.7;
  detectionThresholdMin = ambientNoiseLevel - 0.7;

  Serial.print("Ambient: ");
  Serial.print(ambientNoiseLevel, 3);
  Serial.print("V | Threshold: [");
  Serial.print(detectionThresholdMin, 3);
  Serial.print(" - ");
  Serial.print(detectionThresholdMax, 3);
  Serial.println("]");
}

float readAverageVoltage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(1);
  }
  return (float)sum / samples * (5.0 / 1023.0);
}

// Send fault info to ESP8266 → which forwards to FastAPI
void forwardToServer(String device, String status, float voltage) {
  String payload = "{\"device\":\"" + device + "\",\"status\":\"" + status + "\",\"voltage\":" + String(voltage, 2) + "}";
  ESP.println(payload);
  Serial.print("➡️ Sent to ESP: ");
  Serial.println(payload);
}
