#include <Arduino.h>


namespace configs
{
  const int levelChangeThreshold = 100;
  const byte preamble = 178;
  const int pulseWidthMillis = 5;
  const int receivePin = A1;
}


void setup() {
  Serial.begin(9600); // Debug
}


byte getTransmissionChannel(int previousReading) {
  bool previousBit = 0;
  int channel = 0;
  for (byte i = 0; i < 8; i++) {
    delay(configs::pulseWidthMillis);
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


byte addSignalBit(byte signal) {
  static bool previousBit = 0;
  static int previousReading = 0;
  delay(configs::pulseWidthMillis);
  int currentReading = analogRead(configs::receivePin);
  signal = signal << 1;
  if (
    (previousBit &&
      (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
    ||
    (!previousBit &&
      (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
  ) { signal |= 1; }
  previousBit = signal & 1;
  previousReading = currentReading;
  return signal;
}


bool getSignalBit() {
  static bool previousBit = 0;
  static int previousReading = 0;

  delay(configs::pulseWidthMillis);
  int currentReading = analogRead(configs::receivePin);
  if (
    (previousBit &&
      (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
    ||
    (!previousBit &&
      (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
  ) { previousBit = 1; }
  else { previousBit = 0; } //Signal is LOW

  previousReading = currentReading;
  return previousBit;
}


void loop() {
  // static byte receiverChannel = 4;
  static byte transmissionChannel = 0;
  static byte samplePreamble = 0;

  samplePreamble = (samplePreamble << 1) | getSignalBit();

  if (samplePreamble == configs::preamble) {
    // for (byte i = 0; i < 8; i++) {
    //   transmissionChannel = (transmissionChannel << 1) | getSignalBit();
    // }
    transmissionChannel = getTransmissionChannel(analogRead(configs::receivePin));

    Serial.println(transmissionChannel); //DEBUG
  }
}