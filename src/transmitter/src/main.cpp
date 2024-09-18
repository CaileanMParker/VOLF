#include <Arduino.h>


namespace configs
{
  const int baud = 9600;
  const boolean preamble[8] = {1, 0, 1, 1, 0, 0, 1, 0};
  const int transmissionDelay = 5;
  const int transmitPin = 3;
}


void transmitChannel(int channel) {
  for(byte i = 0; i < 8; i++) {
    digitalWrite(configs::transmitPin, configs::preamble[i]);
    delay(configs::transmissionDelay);
  }
  for(byte i = 0; i < 8; i++) {
    digitalWrite(configs::transmitPin, (channel >> i) & 1);
    delay(configs::transmissionDelay);
  }
  digitalWrite(configs::transmitPin, LOW);
}


void setup() {
  digitalWrite(configs::transmitPin, LOW);
  pinMode(configs::transmitPin, OUTPUT);

  Serial.begin(configs::baud);
  while (!Serial) { ; }
}


void loop() {
  if (Serial.available() > 0) {
    char inChar = Serial.read();
    if (isDigit(inChar)) { transmitChannel(inChar - '0'); }
    Serial.write(inChar);
    Serial.flush();
  }
}