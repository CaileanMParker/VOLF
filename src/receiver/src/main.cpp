// TODO: Refactor
#include "receiver.h"


int awaitPreamble() {
  int currentReading;
  bool previousBit = 0;
  int previousReading = 0;
  byte samplePreamble = 0;
  while (samplePreamble != configs::preamble) {
    delay(configs::pulseWidthMillis);
    currentReading = analogRead(configs::receivePin);
    samplePreamble = samplePreamble << 1;
    if (
      (previousBit &&
        (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
      ||
      (!previousBit &&
        (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
    ) {
      samplePreamble |= 1;
      previousBit = 1;
    }
    else { previousBit = 0; } // Signal is LOW
    previousReading = currentReading;
  }
  return currentReading;
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

#ifdef DEBUG
  Serial.print("Transmission channel: ");
  Serial.println(channel);
#endif

  return channel;
}


void incrementChannel() {
  receiverChannel++;
  if (receiverChannel > 9) { receiverChannel = 1; }
  toggleAudio();
#ifdef DEBUG
  Serial.print("Receiver channel: ");
  Serial.println(receiverChannel);
#endif
}


void toggleAudio() {
  digitalWrite(configs::gateControlPin, HIGH);
  if (transmissionChannel != receiverChannel && transmissionChannel > 0) {
    digitalWrite(configs::gateControlPin, LOW);
  }
}


void setup() {
  pinMode(configs::gateControlPin, OUTPUT);
  digitalWrite(configs::gateControlPin, HIGH);
  pinMode(configs::channelTogglePin, INPUT);
  attachInterrupt(
    digitalPinToInterrupt(configs::channelTogglePin),
    incrementChannel,
    FALLING
  );

#ifdef DEBUG
  Serial.begin(9600);
#endif
}


void loop() {
  int currentReading = awaitPreamble();
  transmissionChannel = getTransmissionChannel(currentReading);
  toggleAudio();
}