#pragma once

#include <Arduino.h>

// #define DEBUG
// #define VERBOSE_DEBUG
// #define READONLY

namespace channels {
  extern byte receiver; // Channel on which the receiver will relay audio
  extern byte transmitter; // Channel on which incoming audio is being transmitted
}

namespace configs {
  inline constexpr uint8_t channelTogglePin = 2;
  inline constexpr uint8_t gateControlPin = 13;
  inline constexpr uint16_t levelChangeThreshold = 100;
  inline constexpr byte preamble = 178; // 10110010
  inline constexpr uint32_t pulseWidthMillis = 5;
  inline constexpr uint8_t receivePin = A1;
}

void awaitPreamble();
byte getTransmissionChannel();
void incrementChannel();

inline byte readBitIntoByte(byte receivedByte) {
  static bool previousBit = 0;
  static uint16_t previousReading = 0;

  delay(configs::pulseWidthMillis);
  static uint16_t currentReading = analogRead(configs::receivePin);
  receivedByte <<= 1;
  if (
    (previousBit &&
      (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
    ||
    (!previousBit &&
      (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
  ) {
    receivedByte |= 1;
    previousBit = 1;
  }
  else previousBit = 0; // Signal is LOW
  previousReading = currentReading;

#ifdef VERBOSE_DEBUG
    char outString[7];
    sprintf(outString, "%i %i %i", currentReading, previousBit, samplePreamble);
    Serial.println(outString);
#endif

  return receivedByte;
}

void readContinual(int delayMillis, long sampleSize);
void toggleAudio();