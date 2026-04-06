#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// Sensor pins - now only one sensor
const int analogPin = A0;   // Single sensor
const int ledPin = 13;      // LED for sensor
const int calibrationTime = 5000; // 5 seconds calibration
const int sampleCount = 20;

// nRF24L01 setup
RF24 radio(2, 3);  // CE, CSN pins (change according to your wiring)
const byte addresses[][6] = {"1Node", "2Node"};

// Sensor variables
float detectionThresholdMax = 1.0;
float detectionThresholdMin = 1.0;
float ambientNoiseLevel = 0;
bool isCalibrated = false;
bool powerCutDetected = false;
unsigned long lastTransmissionTime = 0;
const unsigned long transmissionInterval = 2000; // Send every 2 seconds if power cut
bool headConnected = false;
unsigned long connectionCheckTime = 0;
const unsigned long connectionCheckInterval = 3000; // Check connection every 3 seconds

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  
  // Initialize nRF24L01
  if (!radio.begin()) {
    Serial.println("NRF24 hardware not responding!");
    while (1);
  }
  radio.openWritingPipe(addresses[1]);     // Send to head node
  radio.openReadingPipe(1, addresses[0]);  // Receive from head node
  radio.setPALevel(RF24_PA_LOW);
  radio.setRetries(3, 5); // Set retries with 750us delay and 5 retries
  radio.startListening();
  
  Serial.println("=== Live Wire Detector (Single Sensor) ===");
  
  // Wait for head connection before calibration
  waitForHeadConnection();
  
  // Calibrate sensor
  calibrateSensor();
}

void loop() {
  float currentVoltage = readAverageVoltage(analogPin, sampleCount);
  
  bool liveWireDetected = (currentVoltage > detectionThresholdMax || currentVoltage < detectionThresholdMin);
  
  digitalWrite(ledPin, liveWireDetected ? HIGH : LOW);
  
  // Check if power cut is detected
  bool currentPowerCut = liveWireDetected;
  
  // If power cut status changed or it's time to send update
  if (currentPowerCut != powerCutDetected || (currentPowerCut && millis() - lastTransmissionTime > transmissionInterval)) {
    powerCutDetected = currentPowerCut;
    lastTransmissionTime = millis();
    
    if (powerCutDetected) {
      if (sendPowerCutAlert()) {
        Serial.println("Power cut alert sent successfully");
      } else {
        Serial.println("Power cut alert failed to send");
        headConnected = false;
      }
    } else {
      if (sendPowerRestored()) {
        Serial.println("Power restored message sent successfully");
      } else {
        Serial.println("Power restored message failed to send");
        headConnected = false;
      }
    }
  }
  
  // Display status with timestamp
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 1000) {
    lastPrint = millis();
    
    Serial.print("Time: ");
    Serial.print(millis() / 1000);
    Serial.print("s");
    
    // Sensor data
    Serial.print(" | Sensor: ");
    Serial.print(currentVoltage, 3);
    Serial.print("V ");
    Serial.print(liveWireDetected ? "⚠️" : "✅");
    
    // Transmission status
    Serial.print(" | TX: ");
    Serial.println(powerCutDetected ? "POWER CUT ALERT" : "Normal");
    
    // Connection status
    Serial.print(" | Connection: ");
    Serial.println(headConnected ? "Connected" : "Disconnected");
  }
  
  // Check for incoming messages
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    String message = String(text);
    
    Serial.print("Received: ");
    Serial.println(message);
    
    if (message.indexOf("HEARTBEAT") != -1) {
      // Respond to heartbeat
      String response = "ALIVE:" + String(powerCutDetected ? "POWER_CUT" : "NORMAL");
      if (sendMessage(response)) {
        Serial.println("Heartbeat response sent");
      } else {
        Serial.println("Heartbeat response failed");
        headConnected = false;
      }
    }
    else if (message.indexOf("CONNECTION_REQUEST") != -1) {
      // Respond to connection request
      if (sendMessage("NODE_READY")) {
        Serial.println("Connection response sent");
        headConnected = true;
      }
    }
    else if (message.indexOf("ACK") != -1) {
      handleAck(message);
    }
  }
  
  // Periodically check connection status
  if (millis() - connectionCheckTime > connectionCheckInterval) {
    connectionCheckTime = millis();
    if (!headConnected) {
      Serial.println("Head disconnected - attempting to reconnect");
      waitForHeadConnection();
    }
  }
  
  delay(100);
}

void waitForHeadConnection() {
  Serial.println("Waiting for head connection...");
  
  unsigned long startTime = millis();
  bool connectionEstablished = false;
  
  while (!connectionEstablished && millis() - startTime < 30000) { // Wait up to 30 seconds
    // Listen for connection request
    if (radio.available()) {
      char text[32] = "";
      radio.read(&text, sizeof(text));
      String message = String(text);
      
      if (message.indexOf("CONNECTION_REQUEST") != -1) {
        // Send response
        if (sendMessage("NODE_READY")) {
          headConnected = true;
          connectionEstablished = true;
          Serial.println("Head connection established!");
          break;
        }
      }
    }
    
    if (!connectionEstablished) {
      Serial.println("No connection request from head, waiting...");
      delay(1000);
    }
  }
  
  if (!connectionEstablished) {
    Serial.println("Failed to establish connection with head");
    // Continue with node-only operation
    headConnected = false;
  }
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
  
  detectionThresholdMax = ambientNoiseLevel + 0.7; // 0.7V above ambient
  detectionThresholdMin = ambientNoiseLevel - 0.7;
  
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

bool sendPowerCutAlert() {
  String alertMsg = "POWER_CUT:ALERT";
  return sendMessage(alertMsg);
}

bool sendPowerRestored() {
  String normalMsg = "POWER_RESTORED:OK";
  return sendMessage(normalMsg);
}

bool sendMessage(String message) {
  radio.stopListening();
  bool success = radio.write(message.c_str(), message.length() + 1);
  radio.startListening();
  return success;
}

void handleAck(String message) {
  Serial.println("ACK received: " + message);
  // You can add specific handling for different ACK types if needed
}
