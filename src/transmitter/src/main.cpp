#include <Arduino.h>


namespace configs
{
  const int baud = 9600;
  const byte preamble = 178; // 10110010
  const int pulseWidthMillis = 5;
  const int transmitPin = 13;
}


void transmitChannel(int channel) {
  for(int i = 7; i >= 0; i--) {
    digitalWrite(configs::transmitPin, (configs::preamble >> i) & 1);
    delay(configs::pulseWidthMillis);
  }
  // for(int i = 7; i >= 0; i--) {
  for(byte i = 0; i < 8; i++) {
    digitalWrite(configs::transmitPin, (channel >> i) & 1);
    delay(configs::pulseWidthMillis);
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