#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(2, 3);

const byte HEAD_ID = 0;
const byte MIDDLE_ID = 1;
const byte LAST_ID = 2;

const int switchPin = 7;

// Pipes
const byte addresses[][6] = {"1Node", "2Node", "3Node"};

void setup() {
  pinMode(switchPin, INPUT);
  Serial.begin(9600);

  if (!radio.begin()) {
    Serial.println("NRF24 hardware not responding!");
    while (1);
  }

  radio.openWritingPipe(addresses[1]); // Send to Middle
  radio.openReadingPipe(1, addresses[2]); // Receive for Last
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  Serial.println("Last Node started...");
}

void loop() {
  // Check switch for alert
  if (digitalRead(switchPin) == HIGH) {
    sendAlert();
  }

  // Receive heartbeat or messages
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    Serial.print("Received: ");
    Serial.println(text);

    String msg = String(text);
    if (msg.indexOf("->2") != -1) {
      replyToHead("ACK from Last");
    }
  }
}

void replyToHead(const char* reply) {
  radio.stopListening();
  radio.write(reply, strlen(reply) + 1); // send to Middle
  radio.startListening();
}

void sendAlert() {
  String alertMsg = "ALERT from Node " + String(LAST_ID);
  replyToHead(alertMsg.c_str());
}
