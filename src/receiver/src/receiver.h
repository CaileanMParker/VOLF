#pragma once

#define DEBUG
// #define VERBOSE_DEBUG
// #define READONLY

byte receiverChannel = 1;
byte transmissionChannel = 0;

namespace configs
{
  inline constexpr int channelTogglePin = 2;
  inline constexpr int gateControlPin = 13;
  inline constexpr int levelChangeThreshold = 100;
  inline constexpr byte preamble = 178; // 10110010
  inline constexpr int pulseWidthMillis = 5;
  inline constexpr int receivePin = A1;
}

int awaitPreamble();
byte getTransmissionChannel(int previousReading);
void incrementChannel();
void readContinual(int delayMillis, long sampleSize);
void toggleAudio();