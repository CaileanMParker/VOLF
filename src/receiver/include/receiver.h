#pragma once

#include <Arduino.h>

// #define DEBUG
// #define VERBOSE_DEBUG
// #define READONLY


/// @brief Global channel values for the receiver
namespace channels {
  /// @brief Channel on which the receiver will relay audio
  extern byte receiver;

  /// @brief Channel on which incoming audio is being transmitted
  extern byte transmitter;
}

/// @brief Global configuration values for the receiver
namespace configs {
  /// @brief The pin to which the channel toggle switch is connected
  inline constexpr uint8_t channelTogglePin = 2;

  /// @brief The pin to which the audio gate control is connected
  inline constexpr uint8_t gateControlPin = 13;

  /// @brief The threshold at which a change in "digital" signal level is
  /// detected
  inline constexpr uint16_t levelChangeThreshold = 100;

  /// @brief The byte (bit sequence: 10110010) which, when received, indicates
  /// that the next byte received will be the channel
  inline constexpr byte preamble = 178;

  /// @brief The duration of digital signal pulses in milliseconds
  inline constexpr uint32_t pulseWidthMillis = 5;

  /// @brief The pin on which the incoming Lifi signal is sampled
  inline constexpr uint8_t receivePin = A1;
}

/**
 * @brief Function called by the Arduino framework once on startup which
 * configures the initial state of the device
 */
void setup();

/**
 * @brief Blocks until the preamble is detected
 */
void awaitPreamble();

/**
 * @brief Read the next byte transmitted representing the incoming channel
 * @return The channel on which incoming audio will be transmitted
 */
byte getTransmissionChannel();

/**
 * @brief Increment the channel on which audio is being received and toggle
 * audio accordingly
 */
void incrementChannel();

/**
 * @brief Shift the next bit received into the end of the given byte
 * @param receivedByte The byte tinto which the received bit will be shifted
 * @return The byte with the next bit shifted into it
 */
inline byte readBitIntoByte(byte receivedByte) {
  static bool previousBit = 0;
  static uint16_t previousReading = 0;

  delay(configs::pulseWidthMillis);
  static uint16_t currentReading = analogRead(configs::receivePin);
  receivedByte <<= 1;
  if (
    (previousBit &&
      (currentReading > (previousReading - configs::levelChangeThreshold))) //Signal stayed HIGH
    ||
    (!previousBit &&
      (currentReading >= (previousReading + configs::levelChangeThreshold))) //Signal became HIGH
  ) {
    receivedByte |= 1;
    previousBit = 1;
  }
  else previousBit = 0; // Signal is LOW
  previousReading = currentReading;

#ifdef VERBOSE_DEBUG
    char outString[7];
    sprintf(outString, "%i %i %i", currentReading, previousBit, receivedByte);
    Serial.println(outString);
#endif

  return receivedByte;
}



/**
 * @brief Read a number of samples from the analog pin at a given interval
 * before sending them over serial, continues forever
 * @param delayMillis The interval at which samples will be read
 * @param sampleSize The number of samples to read before sending them over
 * serial
 */
void readContinual(int delayMillis, long sampleSize);

/**
 * @brief Toggle the audio gate control pin
 */
void toggleAudio();

/**
 * @brief Function called by the Arduino framework continually after setup
 * which defines standard device operation
 */
void loop();