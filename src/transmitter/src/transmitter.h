#ifndef TRANSMITTER_HEADER
#define TRANSMITTER_HEADER

namespace configs
{
  const int baud = 9600;
  const byte preamble = 178; // 10110010
  const int pulseWidthMillis = 5;
  const int transmitPin = 13;
}

void transmitChannel(int channel);

#endif