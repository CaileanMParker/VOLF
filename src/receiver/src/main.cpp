#include "receiver.h"


uint8_t channels::receiver = 1;
uint8_t channels::transmitter = 9;


void setup() {
  pinMode(configs::gateControlPin, OUTPUT);
  pinMode(configs::channelTogglePin, INPUT);

  digitalWrite(configs::gateControlPin, HIGH); // Audio gate is initially open

  attachInterrupt(
    digitalPinToInterrupt(configs::channelTogglePin),
    incrementChannel,
    FALLING
  );

#if defined(DEBUG) || defined(READONLY) || defined(VERBOSE_DEBUG)
  Serial.begin(9600);
  Serial.print("Receiver initialized on channel: ");
  Serial.println(channels::receiver);
#endif
}


void awaitPreamble() {
  byte samplePreamble = 0;
  while (samplePreamble != configs::preamble) {
    samplePreamble = readBitIntoByte(samplePreamble);
  }
}


byte getTransmissionChannel() {
  constexpr uint8_t firstBitPosition = 0;
  constexpr uint8_t lastBitPosition = 7;

  byte channel = 0;
  for (int i = firstBitPosition; i <= lastBitPosition; i++) {
    channel = readBitIntoByte(channel);
  }

#ifdef DEBUG
  Serial.print("Transmission channel: ");
  Serial.println(channel);
#endif

  return channel;
}


void incrementChannel() {
  channels::receiver++;
  if (channels::receiver > 9) { channels::receiver = 1; }
  toggleAudio();

#ifdef DEBUG
  Serial.print("Receiver channel: ");
  Serial.println(channels::receiver);
#endif
}


void readContinual(uint32_t delayMillis, uint64_t sampleSize) {
  while (sampleSize == 1) {
    Serial.println(analogRead(configs::receivePin));
    delay(delayMillis);
  }

  uint16_t readings[sampleSize];
  while (true) {
    for (uint64_t i = 0ULL; i < sampleSize; i++) {
      readings[i] = analogRead(configs::receivePin);
      delay(delayMillis);
    }
    for (uint64_t i = 0ULL; i < sampleSize; i++) {
      Serial.println(readings[i]);
    }
    Serial.println();
  }
}


void toggleAudio() {
  if (channels::transmitter != channels::receiver && channels::transmitter > 0) {
    digitalWrite(configs::gateControlPin, LOW); // Close the audio gate
  }
  else {
    digitalWrite(configs::gateControlPin, HIGH); // Open the audio gate
  }
}


void loop() {
#ifdef READONLY
  readContinual(configs::pulseWidthMillis, 1000);
#endif

  awaitPreamble();
  channels::transmitter = getTransmissionChannel();
  toggleAudio();
}