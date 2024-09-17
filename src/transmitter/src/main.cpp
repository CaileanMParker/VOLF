#include <Arduino.h>


namespace configs
{
    const int baud = 9600;
    const int transmitPin = 3;
}


void transmit_channel(int channel) {
  digitalWrite(configs::transmitPin, HIGH);
  delay(5);
  digitalWrite(configs::transmitPin, LOW);
  delay(5);
  digitalWrite(configs::transmitPin, HIGH);
  delay(5);
  digitalWrite(configs::transmitPin, HIGH);
  delay(5);
  digitalWrite(configs::transmitPin, LOW);
  delay(5);
  digitalWrite(configs::transmitPin, LOW);
  delay(5);
  digitalWrite(configs::transmitPin, HIGH);
  delay(5);
  digitalWrite(configs::transmitPin, LOW);
  delay(5);
  for(byte i = 0; i < 8; i++) {
    digitalWrite(configs::transmitPin, (channel >> i) & 1);
    delay(5);
  }
}


void setup() {
  digitalWrite(configs::transmitPin, LOW);
  pinMode(configs::transmitPin, OUTPUT);

  Serial.begin(configs::baud);
  while (!Serial) { ; }
}


void loop() {
  char inChar;
  while (Serial.available() > 0) {
    inChar = Serial.read();
    if (isDigit(inChar)) { transmit_channel(inChar - '0'); }
    Serial.write(inChar);
    Serial.flush();
  }
}