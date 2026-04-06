// Jai Shree Ram
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// nRF24L01 setup
RF24 radio(2, 3);  // CE, CSN pins (change according to your wiring)
const byte addresses[][6] = {"1Node", "2Node"};

// Buzzer pin
const int buzzerPin = A1;

// Head device sensor pin
const int headSensorPin = A0;

// Sensor calibration variables
float headDetectionThresholdMax = 1.0;
float headDetectionThresholdMin = 1.0;
float headAmbientNoiseLevel = 0;
const int headSampleCount = 20;
bool headPowerFaultDetected = false; // TRUE = fault

// Variables
unsigned long lastHeartbeatTime = 0;
const unsigned long heartbeatInterval = 10000; // 10 seconds
unsigned long lastAlertTime = 0;
bool powerFaultStatus = false;
bool disturbingSoundActive = false;
bool nodeConnected = false;
unsigned long connectionCheckTime = 0;
const unsigned long connectionCheckInterval = 3000; // Check connection every 3 seconds

void setup() {
  Serial.begin(9600);

  // Initialize buzzer
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  // Initialize head sensor
  pinMode(headSensorPin, INPUT);

  // Initialize nRF24L01
  if (!radio.begin()) {
    Serial.println("NRF24 hardware not responding!");
    while (1);
  }
  radio.openWritingPipe(addresses[0]);     // Send to sensor node
  radio.openReadingPipe(1, addresses[1]);  // Receive from sensor node
  radio.setPALevel(RF24_PA_LOW);
  radio.setRetries(3, 5);
  radio.startListening();

  Serial.println("Head Node started...");

  // Wait for node connection before calibration
  waitForNodeConnection();

  // Calibrate head sensor
  calibrateHeadSensor();

  Serial.println("System Normal - Waiting...");
}

void loop() {
  // Check head device sensor for power fault
  checkHeadSensor();

  // Send heartbeat every 10 seconds
  if (millis() - lastHeartbeatTime > heartbeatInterval) {
    if (sendHeartbeat()) {
      lastHeartbeatTime = millis();
    } else {
      Serial.println("Heartbeat failed - node may be disconnected");
      nodeConnected = false;
      waitForNodeConnection();
    }
  }

  // Check for incoming messages
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    String message = String(text);

    Serial.print("Received: ");
    Serial.println(message);

    if (message.indexOf("POWER_CUT") != -1) {
      handlePowerCutAlert();
      sendAck("ALERT_RECEIVED");
    } 
    else if (message.indexOf("POWER_RESTORED") != -1) {
      handlePowerRestored();
      sendAck("RESTORE_RECEIVED");
    }
    else if (message.indexOf("ALIVE") != -1) {
      handleAliveResponse(message);
      sendAck("ALIVE_RECEIVED");
    }
    else if (message.indexOf("ACK") != -1) {
      handleAck(message);
    }
    else if (message.indexOf("NODE_READY") != -1) {
      nodeConnected = true;
      Serial.println("Node connection confirmed");
      sendAck("HEAD_READY");
    }
  }

  // Periodically check connection status
  if (millis() - connectionCheckTime > connectionCheckInterval) {
    connectionCheckTime = millis();
    if (!nodeConnected) {
      Serial.println("Node disconnected - attempting to reconnect");
      waitForNodeConnection();
    }
  }

  // Handle disturbing sound if active
  if (disturbingSoundActive) {
    unsigned long currentTime = millis();
    static unsigned long lastToneChange = 0;

    if (currentTime - lastToneChange > 200) {
      lastToneChange = currentTime;
      int frequency = random(500, 2000);
      tone(buzzerPin, frequency, 190);
    }

    if (currentTime - lastAlertTime > 10000) {
      disturbingSoundActive = false;
      noTone(buzzerPin);
    }
  }

  delay(300); // slower so values are readable
}

void waitForNodeConnection() {
  Serial.println("Waiting for node connection...");

  unsigned long startTime = millis();
  bool connectionEstablished = false;

  while (!connectionEstablished && millis() - startTime < 30000) {
    radio.stopListening();
    String connectionMsg = "CONNECTION_REQUEST";
    if (radio.write(connectionMsg.c_str(), connectionMsg.length() + 1)) {
      Serial.println("Connection request sent");
    }
    radio.startListening();

    unsigned long responseWaitStart = millis();
    while (millis() - responseWaitStart < 2000) {
      if (radio.available()) {
        char text[32] = "";
        radio.read(&text, sizeof(text));
        String message = String(text);

        if (message.indexOf("NODE_READY") != -1) {
          nodeConnected = true;
          connectionEstablished = true;
          Serial.println("Node connection established!");
          tone(buzzerPin, 1500, 500);
          delay(600);
          break;
        }
      }
      delay(100);
    }

    if (!connectionEstablished) {
      Serial.println("No response from node, retrying...");
      delay(1000);
    }
  }

  if (!connectionEstablished) {
    Serial.println("Failed to establish connection with node, running head-only mode");
    nodeConnected = false;
  }
}

void checkHeadSensor() {
  float currentVoltage = readAverageVoltage(headSensorPin, headSampleCount);

  // NEW LOGIC: Power present (live wire detected) = FAULT
  bool currentFault = (currentVoltage > headDetectionThresholdMax || currentVoltage < headDetectionThresholdMin);

  if (currentFault != headPowerFaultDetected) {
    headPowerFaultDetected = currentFault;

    if (headPowerFaultDetected) {
      handlePowerCutAlert();
    } else {
      handlePowerRestored();
    }
  }
}

float readAverageVoltage(int pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(1);
  }
  return (float)sum / samples * (5.0 / 1023.0);
}

void calibrateHeadSensor() {
  Serial.println("Calibrating head sensor... Ensure no live wires nearby");

  for (int i = 5; i > 0; i--) {
    Serial.print(String(i) + "...");
    delay(1000);
  }
  Serial.println();

  headAmbientNoiseLevel = readAverageVoltage(headSensorPin, 125);

  headDetectionThresholdMax = headAmbientNoiseLevel + 0.7;
  headDetectionThresholdMin = headAmbientNoiseLevel - 0.7;

  Serial.println("Calibration complete!");
  Serial.print("Ambient Noise Level: ");
  Serial.print(headAmbientNoiseLevel, 3);
  Serial.println(" V");
  Serial.print("Threshold Range: [");
  Serial.print(headDetectionThresholdMin, 3);
  Serial.print(" V - ");
  Serial.print(headDetectionThresholdMax, 3);
  Serial.println(" V]");
}

bool sendHeartbeat() {
  String heartbeatMsg = "HEARTBEAT:REQUEST";
  radio.stopListening();
  bool success = radio.write(heartbeatMsg.c_str(), heartbeatMsg.length() + 1);
  radio.startListening();

  if (success) {
    Serial.println("Heartbeat sent");
    return true;
  } else {
    Serial.println("Heartbeat failed to send");
    return false;
  }
}

void sendAck(String ackType) {
  String ackMsg = "ACK:" + ackType;
  radio.stopListening();
  if (radio.write(ackMsg.c_str(), ackMsg.length() + 1)) {
    Serial.println("ACK sent: " + ackType);
  } else {
    Serial.println("ACK failed: " + ackType);
  }
  radio.startListening();
}

void handleAck(String message) {
  Serial.println("ACK received: " + message);
}

void handlePowerCutAlert() {
  powerFaultStatus = true;
  lastAlertTime = millis();
  disturbingSoundActive = true;

  Serial.println("⚠️ FAULT DETECTED: POWER PRESENT on Line!");
}

void handlePowerRestored() {
  powerFaultStatus = false;
  disturbingSoundActive = false;
  noTone(buzzerPin);

  Serial.println("✅ System Normal (No Power Detected)");
  tone(buzzerPin, 1000, 200);
  delay(1000);
}

void handleAliveResponse(String message) {
  Serial.println("Alive response: " + message);

  if (message.indexOf("POWER_CUT") != -1 && !powerFaultStatus) {
    handlePowerCutAlert();
  }

  tone(buzzerPin, 1500, 1000);

  if (powerFaultStatus) {
    Serial.println("⚠️ STATUS: Fault (Power Detected)");
  } else {
    Serial.println("✅ STATUS: Normal");
  }
}
