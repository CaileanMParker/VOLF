#include <Arduino.h>


namespace configs
{
  const int levelChangeThreshold = 100;
  const boolean preamble[8] = {1, 0, 1, 1, 0, 0, 1, 0};
  const byte preambleLength = sizeof(preamble)/sizeof(*preamble);
  const int receivePin = A1;
  const int transmissionDelay = 5;
}


void setup() {
  Serial.begin(9600);
}


byte getTransmissionChannel(int previousReading) {
  bool previousBit = 0;
  int channel = 0;
  for (byte i = 0; i < 8; i++) {
    delay(configs::transmissionDelay);
    int currentReading = analogRead(configs::receivePin);
    if (
      (previousBit &&
        (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
      ||
      (!previousBit &&
        (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
    ) {
      channel |= (1 << i);
      previousBit = 1;
    } else { //Signal is LOW
      previousBit = 0;
    }
    previousReading = currentReading;
  }
  return channel;
}


void loop() {
  static char outString[8]; // DEBUG
  static int readings[9];

  static int previousReading = 0;
  static byte preambleIndex = 1;
  // static byte receiverChannel = 4;
  static byte transmissionChannel = 0;


  int currentReading = analogRead(configs::receivePin);

  if (
    (configs::preamble[preambleIndex] && // Signal should be HIGH
      (
        ( //Signal was LOW, but came HIGH
          !configs::preamble[preambleIndex-1] &&
          (currentReading >= (previousReading + configs::levelChangeThreshold))
        ) ||
        ( // Signal stayed HIGH
          configs::preamble[preambleIndex-1] &&
          (currentReading > (previousReading - configs::levelChangeThreshold))
        )
      )
    ) ||
    (!configs::preamble[preambleIndex] && // Signal should be LOW
      (
        ( // Signal was HIGH, but came LOW
          configs::preamble[preambleIndex-1] &&
          (currentReading <= (previousReading - configs::levelChangeThreshold))
        ) ||
        ( // Signal stayed LOW
          !configs::preamble[preambleIndex-1] &&
          (currentReading < (previousReading + configs::levelChangeThreshold))
        )
      )
    )
  ) {
    readings[preambleIndex] = currentReading; // DEBUG

    preambleIndex++;
    if (preambleIndex == configs::preambleLength) {
      preambleIndex = 1;
      transmissionChannel = getTransmissionChannel(currentReading);
      Serial.println(transmissionChannel);
    }
  } else if (preambleIndex > 1) {
    readings[preambleIndex] = currentReading;  // DEBUG
    for (byte i = 1; i <= preambleIndex; i++) {
      sprintf(outString, "%i %i", i, readings[i]);
      Serial.println(outString);
    }

    preambleIndex = 1;
  }
  previousReading = currentReading;
  delay(configs::transmissionDelay);
}