#pragma once

#include <Arduino.h>

// #define DEBUG

/// @brief Global configuration values for the transmitter
namespace configs {
  /// @brief The byte (bit sequence: 10110010) which, when transmitted,
  /// indicates that the next byte sent will be the channel
  inline constexpr byte preamble = 178; // 10110010

  /// @brief The duration of digital signal pulses in milliseconds
  inline constexpr unsigned long pulseWidthMillis = 5;

  /// @brief The pin on which the outgoing signals are transmitted
  inline constexpr uint8_t transmitPin = 13;
}

/**
 * @brief Function called by the Arduino framework once on startup which
 * configures the initial state of the device
 */
void setup();

/**
 * @brief Transmit a byte of data over the configured pin
 * @param byteToTransmit The byte to transmit
 */
void transmitByte(byte byteToTransmit);

/**
 * @brief Transmit the preamble and subsequently a channel
 * @param channel The channel to transmit
 */
void transmitChannel(byte channel);

/**
 * @brief Function called by the Arduino framework continually after setup
 * which defines standard device operation
 */
void loop();