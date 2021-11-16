# Hermes Audio Server

[![Build status](https://api.travis-ci.com/koenvervloesem/hermes-audio-server.svg?branch=master)](https://travis-ci.com/koenvervloesem/hermes-audio-server) [![Maintainability](https://api.codeclimate.com/v1/badges/9ae3a46a15a85c8b44f3/maintainability)](https://codeclimate.com/github/koenvervloesem/hermes-audio-server/maintainability) [![Code quality](https://api.codacy.com/project/badge/Grade/02647c1d9d214b8a97ed124ccf48839f)](https://www.codacy.com/app/koenvervloesem/hermes-audio-server) [![Python versions](https://img.shields.io/badge/python-3.5|3.6|3.7-blue.svg)](https://www.python.org) [![PyPI package version](https://img.shields.io/pypi/v/hermes-audio-server.svg)](https://pypi.python.org/pypi/hermes-audio-server) [![GitHub license](https://img.shields.io/github/license/koenvervloesem/hermes-audio-server.svg)](https://github.com/koenvervloesem/hermes-audio-server/blob/master/LICENSE)

Rhasspy Desktop Satellite server implements the audio recorder and player parts of the [Hermes protocol](https://docs.snips.ai/reference/hermes) defined by [Snips](http://snips.ai) as implemented by [Rhasspy](https://rhasspy.readthedocs.io).

It's meant to be used with [Rhasspy](https://rhasspy.readthedocs.io), an offline, multilingual voice assistant toolkit that works with [Home Assistant](https://www.home-assistant.io) and is completely open source.

With Rhasspy Desktop Satellite, you can use the microphone and speaker of your computer (such as a Raspberry Pi) as remote audio input and output for a Rhasspy system.
As Rhasspy Desktop Satellite is prominently targeted at workstation computers which might know a lot of voice activity (online voice chatting, zoom meetings etc.) it does **not** enable hotword detection by default but relies on external explicit triggers to activate the
Automatic Speech Recognition (ASR) process (see below). 

## System requirements

Rhasspy Desktop Satellite requires Python 3. It has been tested on x86_64 desktops running OpenSuSE LEAP 15.3 and Fedora 35, but in principle it should be cross-platform. Please [open an issue](https://github.com/mcorino/rhasspy-desktop-satellite/issues) on GitHub when you encounter problems or when the software exits with the message that your platform is not supported.

## Installation

You can install Rhasspy Desktop Satellite and its dependencies like this:

```shell
sudo apt install portaudio19-dev
sudo pip3 install rhasspy-desktop-satellite
```

Note: this installs Rhasspy Desktop Satellite globally. If you want to install Rhasspy Desktop Satellite in a Python virtual environment, drop the `sudo`.

## Configuration

Rhasspy Desktop Satellite is configured in the JSON file `/etc/rhasspy-desktop-satellite.json`, which has the following format:

```json
{
    "site": "default",
    "recorder": {
        "enabled": true,
        "device": "default",
        "wakeup": false
    },
    "player": {
        "enabled": true,
        "device": "default"
    },
    "mqtt": {
        "host": "localhost",
        "port": 1883,
        "authentication": {
            "username": "foobar",
            "password": "secretpassword"
        },
        "tls": {
            "ca_certificates": "",
            "client_certificate": "",
            "client_key": ""
        }
    }
}
```

Note that this supposes that you're using authentication and TLS for the connection to your MQTT broker.

All keys in the configuration file are optional. The default behaviour is to connect with `localhost:1883` without authentication and TLS and to use `default` as the site ID and recorder and player enabled for the default audio device. A configuration file for this situation would like like this:

```json
{
    "site": "default",
    "recorder": {
      "enabled": true
    },
    "player": {
      "enabled": true
    },
    "mqtt": {
        "host": "localhost",
        "port": 1883
    }
}
```

By default Rhasspy Desktop Satellite uses the system's default microphone and speaker. This can be configured with the `"device"` attribute of the `"recorder"` and `"player"` configurations.

### Automatic Speech Recognition startup and Wake Word Detection

Wake word (hotword) detection is by default not enabled in Rhasspy Desktop Satellite in order not to cause unintended problems with any other processes on workstations requiring access to
the audio devices and involving voice activity.

To trigger speech recognition in Rhasspy and associated audio capture by Rhasspy Desktop Satellite it is in this case necessary to cause the publication of
an appropriate Hermes MQTT `hermes/hotword<hotword id>/detected` topic with a JSON message payload providing a matching site id by other means. Most typically 
this would be way of a script triggered by some GUI element or hotkey.
The `<hotword id>` should be a valid hotword id recognized by Rhasspy. In case only a single hotword is configured this could be the fixed `default` id otherwise
it should be an actual hotword id (see Rhasspy for more information).
The payload for the topic should contain the following JSON at a minimum:
```json
{
  "siteId": "mySite",
  "modelId": ""
}
```
The `siteId` value should match the configured site id of Rhasspy Desktop Satellite.

Rhasspy Desktop Satellite can also be configured for voice triggered wake word detection by setting the `wakeup` attribute of the `recorder` configuration to `true` as follows:

```json
{
    "site": "default",
    "recorder": {
      "enabled": true,
      "wakeup": true
    },
    "player": {
      "enabled": true
    },
    "mqtt": {
        "host": "localhost",
        "port": 1883
    }
}
```

## Rhasspy Desktop Satellite

You can run the Rhasspy Desktop Satellite like this:

```shell
rhasspy-desktop-satellite
```

## Usage

The command knows the `--help` option that gives you more information about the recognized options. For instance:

```shell
usage: rhasspy-desktop-satellite [-h] [-v] [-V] [-c CONFIG]

rhasspy-desktop-satellite is an audio server implementing the record AND playback part of
    the Hermes protocol.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         use verbose output
  -V, --version         print version information and exit
  -c CONFIG, --config CONFIG
                        configuration file [default: /etc/rhasspy-desktop-satellite.json]
  -d, --daemon          run as daemon
```

## Running as a service
After you have verified that Rhasspy Desktop Satellite works by running the command manually, possibly in verbose mode, it's better to run the command as a service.

It's recommended to run the Rhasspy Desktop Satellite commands as a system user. Create this user without a login shell and without creating a home directory for the user:

```shell
sudo useradd -r -s /bin/false rhasspy-satellite
```

This user also needs access to your audio devices, so add them to the `audio` group:

```shell
sudo usermod -a -G audio rhasspy-satellite
```

Then create a [systemd service file](https://github.com/mcorino/rhasspy-desktop-satellite/tree/master/etc/systemd/system) for the `rhasspy-desktop-satellite` command and copy it to `/etc/systemd/system`.

If you want to run the commands as another user, then cange the lines with `User` and `Group`.

After this, you can start the Rhasspy Desktop Satellite server as a service:

```shell
sudo systemctl start rhasspy-desktop-satellite.service
```

If you want it to start automatically after booting the computer, enable the service with:

```shell
sudo systemctl enable rhasspy-desktop-satellite.service
```

## Known issues / TODO list

*   This project is really a minimal implementation of the audio server part of the Hermes protocol, meant to be used with Rhasspy. It's not a drop-in replacement for snips-audio-server, as it lacks [additional metadata](https://github.com/snipsco/snips-issues/issues/144#issuecomment-494054082) in the WAV frames.

## Changelog

*   0.1.0 (2021-11-16): First public release.

## Credits

This project is derived from the following projects:
* [Hermes Audio Server](https://github.com/koenvervloesem/hermes-audio-server)
* https://github.com/rhasspy/rhasspy-microphone-pyaudio-hermes
* https://github.com/rhasspy/rhasspy-speakers-cli-hermes

## Other interesting projects

If you find Rhasspy Desktop Satellite interesting, have a look at the following projects too:

*   [Rhasspy](https://rhasspy.readthedocs.io): An offline, multilingual voice assistant toolkit that works with [Home Assistant](https://www.home-assistant.io) and is completely open source.
*   [Snips Led Control](https://github.com/Psychokiller1888/snipsLedControl): An easy way to control the leds of your Snips-compatible device, with led patterns when the hotword is detected, the device is listening, speaking, idle, ...
*   [Matrix-Voice-ESP32-MQTT-Audio-Streamer](https://github.com/Romkabouter/Matrix-Voice-ESP32-MQTT-Audio-Streamer): The equivalent of Hermes Audio Server for a Matrix Voice ESP32 board, including LED control and OTA updates.
*   [OpenSnips](https://github.com/syntithenai/opensnips): A collection of open source projects related to the Snips voice platform.

## License

This project is provided by [Martin Corino](mailto:mcorino@m2c-software.nl) as open source software with the MIT license. See the LICENSE file for more information.
