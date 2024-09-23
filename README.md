# VOLF (Voice over LiFi)

## Why?
This project aims to develop a system for simplex audio communications over LiFi in environments where RF-based communications might be unreliable or altogether unavailable.

## How?
We aim to achieve this by modifying pre-existing LED building lights to modulate with, and thus transmit, an audio signal. These modulations are received by a small, body worn device which includes light sensors and would be capable of converting the LiFi signal back into an audio signal. This signal can then be played through a small speaker or earpiece, allowing operators in target environments to hear calls as if through their radios.​

## What?
The primary goal of establishing a simple audio transmission is achievable via the employment of a set of passive circuits (a "transmitter" to encode the audio signal onto the lights and a "receiver" to convert the signal back into audio). Various additional features, however, can be introduced through the inclusion of a microcontroller (MCU) on each circuit respectively, which enable the transmission and interpretation of digital signals over the lights and thus additional control over the circuits and signals. As of now, the only additional feature offered in this repo is the injection of a digital channel prefix into audio transmissions, which the receiver's MCU compares against an internally tracked channel to determine which transmissions to allow through an "audio gate" (transistor or relay)​.

In this repo, you will find schematics for both the passive and MCU-enhanced circuits, as well as the firmware for the MCUs and a program to control transmission channels and stream audio from a computer.

Instructions on using the passive circuit can be found in "docs/passive-circuit-guidance.txt".

Instructions on using the MCU-enhanced circuit can be found in "docs/enhanced-circuit-guidance.txt".

## Who?
- CaileanMParker
- cervonij

Special thanks to Mirko Pavleski for [his project on hackster.io](https://www.hackster.io/mircemk/transferring-data-using-a-led-and-solar-cell-ef8828), which gave us the designs for the base circuits we worked off of!
