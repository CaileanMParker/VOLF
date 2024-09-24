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

  // Transmit the byte bit by bit, back to front
  for(auto i = lastBitPosition; i > firstBitPosition; i--) {
    digitalWrite(configs::transmitPin, (byteToTransmit >> i) & 1);
    delay(configs::pulseWidthMillis);

    // Serial.print(i);
    // Serial.print(" ");
    // Serial.println((byteToTransmit >> i) & 1);
  }
}


void transmitChannel(byte channel) {
#ifdef DEBUG
  Serial.print("Transmitting channel ");
  Serial.write(channel);
  Serial.println();
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