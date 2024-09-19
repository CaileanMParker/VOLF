#pragma once

#include <Arduino.h>

// #define DEBUG

namespace configs {
  inline constexpr byte preamble = 178; // 10110010
  inline constexpr uint32_t pulseWidthMillis = 5;
  inline constexpr uint8_t transmitPin = 13;
}

void transmitByte(byte byteToTransmit);
void transmitChannel(byte channel);