#pragma once

// #define DEBUG

namespace configs
{
  inline constexpr byte preamble = 178; // 10110010
  inline constexpr int pulseWidthMillis = 5;
  inline constexpr int transmitPin = 13;
}

void transmitChannel(int channel);