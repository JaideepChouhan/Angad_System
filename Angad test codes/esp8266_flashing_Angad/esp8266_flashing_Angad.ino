#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "Airtel_deep_5416";
const char* password = "Divy@07052021";

// FastAPI server details
const char* serverIP = "127.0.0.1";  // Change to your server IP
const int serverPort = 8000;
const String apiEndpoint = "http://" + String(serverIP) + ":" + String(serverPort) + "/api/power-data";

// Device configuration - CHANGE THIS FOR EACH DEVICE
const String device_id = "device0001"; // Change to device0002, device0003, etc.

// Status LED
const int statusLed = 2; // Built-in LED

void setup() {
  Serial.begin(115200);
  pinMode(statusLed, OUTPUT);
  
  // Start WiFi connection
  WiFi.begin(ssid, password);
  
  Serial.println();
  Serial.println("=== ESP8266 Power Fault Monitor ===");
  Serial.print("Connecting to WiFi");
  
  // Wait for WiFi connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(statusLed, !digitalRead(statusLed));
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Device ID: ");
  Serial.println(device_id);
  
  digitalWrite(statusLed, HIGH);
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    digitalWrite(statusLed, LOW);
    WiFi.reconnect();
    delay(5000);
    return;
  }
  
  // Simulate fault detection (replace with actual sensor reading)
  simulateFaultDetection();
  
  delay(10000); // Send every 10 seconds
}

void simulateFaultDetection() {
  // Simulate random fault conditions
  float sensor_value = random(100, 1000) / 100.0; // Random value between 1.0 and 10.0
  
  // Only send alert if value exceeds threshold (simulating fault)
  if (sensor_value > 3.0) {
    String fault_type = "overcurrent";
    if (sensor_value > 7.0) {
      fault_type = "short_circuit";
    } else if (sensor_value > 5.0) {
      fault_type = "voltage_drop";
    }
    
    sendFaultAlert(sensor_value, fault_type);
  }
}

void sendFaultAlert(float sensor_value, String fault_type) {
  WiFiClient client;
  HTTPClient http;
  
  // Create JSON document
  DynamicJsonDocument doc(1024);
  doc["device_id"] = device_id;
  doc["fault_type"] = fault_type;
  doc["sensor_value"] = sensor_value;
  doc["timestamp"] = getTimestamp();
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  Serial.println("Sending fault alert:");
  Serial.println(jsonData);
  
  http.begin(client, apiEndpoint);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("HTTP Response code: " + String(httpResponseCode));
    Serial.println("Response: " + response);
    
    // Blink LED on success
    digitalWrite(statusLed, LOW);
    delay(100);
    digitalWrite(statusLed, HIGH);
  } else {
    Serial.println("Error in HTTP request: " + String(httpResponseCode));
    
    // Rapid blink on error
    for(int i = 0; i < 3; i++) {
      digitalWrite(statusLed, LOW);
      delay(100);
      digitalWrite(statusLed, HIGH);
      delay(100);
    }
  }
  
  http.end();
}

String getTimestamp() {
  // Simple timestamp (in production, use RTC or NTP)
  return "2024-01-15T10:00:00Z"; // This will be overwritten by server
}
