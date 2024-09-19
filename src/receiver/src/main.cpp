#include "receiver.h"


byte channels::receiver = 1;
byte channels::transmitter = 9;


void setup() {
  pinMode(configs::gateControlPin, OUTPUT);
  digitalWrite(configs::gateControlPin, HIGH);
  pinMode(configs::channelTogglePin, INPUT);
  attachInterrupt(
    digitalPinToInterrupt(configs::channelTogglePin),
    incrementChannel,
    FALLING
  );

#if defined(DEBUG) || defined(READONLY) || defined(VERBOSE_DEBUG)
  Serial.begin(9600);
  Serial.print("Receiver initialized on channel: ");
  Serial.println(receiverChannel);
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
  for (auto i = firstBitPosition; i <= lastBitPosition; i++) {
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
  Serial.println(receiverChannel);
#endif
}


void readContinual(int delayMillis, uint64_t sampleSize) {
  while (sampleSize == 1) {
    Serial.println(analogRead(configs::receivePin));
    delay(delayMillis);
  }

  int readings[sampleSize];
  while (true) {
    for (auto i = 0ULL; i < sampleSize; i++) {
      readings[i] = analogRead(configs::receivePin);
      delay(delayMillis);
    }
    for (auto i = 0ULL; i < sampleSize; i++) {
      Serial.println(readings[i]);
    }
    Serial.println();
  }
}


void toggleAudio() {
  digitalWrite(configs::gateControlPin, HIGH);
  if (channels::transmitter != channels::receiver && channels::transmitter > 0) {
    digitalWrite(configs::gateControlPin, LOW);
  }
}


void loop() {
#ifdef READONLY
  readContinual(configs::pulseWidthMillis, 1);
#endif

  awaitPreamble();
  channels::transmitter = getTransmissionChannel();
  toggleAudio();
}