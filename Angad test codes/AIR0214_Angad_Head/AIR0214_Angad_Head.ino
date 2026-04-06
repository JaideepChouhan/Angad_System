#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(2, 3);  // CE, CSN

const byte HEAD_ID = 0;
const byte MIDDLE_ID = 1;
const byte LAST_ID = 2;

// Pipes
const byte addresses[][6] = {"1Node", "2Node", "3Node"};

unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 10000; // 10 sec

void setup() {
  Serial.begin(9600);
  if (!radio.begin()) {
    Serial.println("NRF24 hardware not responding!");
    while (1);
  }

  radio.openWritingPipe(addresses[1]); // Send to middle first
  radio.openReadingPipe(1, addresses[0]); // Receive on Head
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  Serial.println("Head Node started...");
}

void loop() {
  // Heartbeat sending every 10 sec
  if (millis() - lastHeartbeat > heartbeatInterval) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }

  // Check incoming messages
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    Serial.print("Received: ");
    Serial.println(text);
  }
}

void sendHeartbeat() {
  radio.stopListening();
  String msg = "HEARTBEAT:" + String(HEAD_ID) + "->" + String(MIDDLE_ID);
  bool ok = false;
  for (int i = 0; i < 3; i++) {
    if (radio.write(msg.c_str(), msg.length() + 1)) {
      ok = true;
      Serial.println("Sent heartbeat to Middle...");
      break;
    }
    delay(5);
  }
  if (!ok) Serial.println("Failed to send heartbeat to Middle!");
  radio.startListening();
}
