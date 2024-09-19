#include "transmitter.h"


void setup() {
  digitalWrite(configs::transmitPin, LOW);
  pinMode(configs::transmitPin, OUTPUT);

  Serial.begin(9600);
  while (!Serial) { ; }
}


void transmitByte(byte byteToTransmit) {
  constexpr uint8_t firstBitPosition = 0;
  constexpr uint8_t lastBitPosition = 7;

  for(auto i = lastBitPosition; i >= firstBitPosition; i--) {
    digitalWrite(configs::transmitPin, (byteToTransmit >> i) & 1);
    delay(configs::pulseWidthMillis);
  }
}


void transmitChannel(byte channel) {
#ifdef DEBUG
  Serial.print("Transmitting channel ");
  Serial.println(channel);
#endif

  transmitByte(configs::preamble);
  transmitByte(channel);
  digitalWrite(configs::transmitPin, LOW);
}


void loop() {
  if (!Serial.available()) return;

  char inChar = Serial.read();
  if (isDigit(inChar)) transmitChannel(static_cast<byte>(inChar));
  Serial.write(inChar);
  Serial.flush();
}