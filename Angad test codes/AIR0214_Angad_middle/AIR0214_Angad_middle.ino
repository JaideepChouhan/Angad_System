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

  radio.openWritingPipe(addresses[2]); // Forward to Last
  radio.openReadingPipe(1, addresses[1]); // Receive for Middle
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();

  Serial.println("Middle Node started...");
}

void loop() {
  // Check switch for alert
  if (digitalRead(switchPin) == HIGH) {
    sendAlert();
  }

  // Forwarding mechanism
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    Serial.print("Received: ");
    Serial.println(text);

    // Check if it's for me or to forward
    String msg = String(text);
    if (msg.indexOf("->1") != -1) {
      // This was addressed to me
      replyToHead("ACK from Middle");
    } else {
      // Forward to next
      forwardMessage(text);
    }
  }
}

void forwardMessage(const char* msg) {
  radio.stopListening();
  for (int i = 0; i < 3; i++) {
    if (radio.write(msg, strlen(msg) + 1)) {
      Serial.print("Forwarded: ");
      Serial.println(msg);
      break;
    }
  }
  radio.startListening();
}

void replyToHead(const char* reply) {
  radio.stopListening();
  radio.openWritingPipe(addresses[0]); // Send back to Head
  radio.write(reply, strlen(reply) + 1);
  radio.openWritingPipe(addresses[2]); // Restore
  radio.startListening();
}

void sendAlert() {
  String alertMsg = "ALERT from Node " + String(MIDDLE_ID);
  forwardMessage(alertMsg.c_str());
}
