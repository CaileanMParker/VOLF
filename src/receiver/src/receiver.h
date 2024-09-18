#ifndef RECEIVER_HEADER
#define RECEIVER_HEADER

#define DEBUG
#define READONLY

#include <Arduino.h>

byte receiverChannel = 1;
byte transmissionChannel = 0;

namespace configs
{
  const int channelTogglePin = 2;
  const int gateControlPin = 13;
  const int levelChangeThreshold = 100;
  const byte preamble = 178; // 10110010
  const int pulseWidthMillis = 5;
  const int receivePin = A1;
}

int awaitPreamble();
byte getTransmissionChannel(int previousReading);
void incrementChannel();
void readContinual(int delayMillis, long sampleSize);
void toggleAudio();

#endif