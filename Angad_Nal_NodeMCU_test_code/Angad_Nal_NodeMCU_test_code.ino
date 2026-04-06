// Jai Shree Ram
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ===== WiFi Config =====
const char* ssid = "Airtel_deep_5416";
const char* password = "Divy@07052021";

// ===== Server Config =====
const char* serverIP = "192.168.1.18"; 
const int serverPort = 8000;
const String apiEndpoint = "http://" + String(serverIP) + ":" + String(serverPort) + "/api/power-data";

// ===== Device Config =====
const String device_id = "head0001";

// ===== Built-in LED =====
const int statusLed = 2;

// ===== nRF24L01 Setup =====
#define CE_PIN  D2
#define CSN_PIN D1
RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

String receivedMessage = "";

void setup() {
  Serial.begin(115200);
  pinMode(statusLed, OUTPUT);
  digitalWrite(statusLed, HIGH);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(statusLed, !digitalRead(statusLed));
  }
  Serial.println("\n✅ WiFi connected!");
  Serial.println("IP: " + WiFi.localIP().toString());
  digitalWrite(statusLed, HIGH);

  // nRF24 Init
  if (!radio.begin()) {
    Serial.println("❌ nRF24 init failed");
    while(1);
  }
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  Serial.println("NodeMCU ready to receive alerts...");
}

void loop() {
  // Receive messages from Arduino
  if (radio.available()) {
    char msg[32] = {0};
    radio.read(&msg, sizeof(msg));
    receivedMessage = String(msg);
    Serial.println("➡️ Received: " + receivedMessage);

    // Blink LED on alert
    if (receivedMessage.startsWith("ALERT")) {
      digitalWrite(statusLed, LOW);
      forwardAlertToServer(receivedMessage);
      delay(200);
      digitalWrite(statusLed, HIGH);
    }
  }
}

// ===== Forward Alert =====
bool forwardAlertToServer(String alertMsg) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected!");
    return false;
  }

  WiFiClient client;
  HTTPClient http;

  DynamicJsonDocument doc(512);
  doc["device_id"] = device_id;
  doc["fault_msg"] = alertMsg;
  doc["timestamp"] = getTimestamp();
  doc["sensor_reading"] = 230.0; // match FastAPI model

  String jsonData;
  serializeJson(doc, jsonData);

  Serial.println("➡️ Sending to server: " + jsonData);

  http.begin(client, apiEndpoint);
  http.addHeader("Content-Type", "application/json");
  int httpResponseCode = http.POST(jsonData);
  http.end();

  if (httpResponseCode > 0) {
    Serial.println("✅ Alert forwarded successfully!");
    return true;
  } else {
    Serial.println("❌ Failed to forward alert!");
    return false;
  }
}

// ===== Timestamp =====
String getTimestamp() {
  unsigned long t = millis() / 1000;
  unsigned long h = t / 3600;
  unsigned long m = (t % 3600) / 60;
  unsigned long s = t % 60;
  char buffer[20];
  snprintf(buffer, sizeof(buffer), "%02lu:%02lu:%02lu", h, m, s);
  return String(buffer);
}
