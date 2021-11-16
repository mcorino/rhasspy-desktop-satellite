"""Classes for the configuration of rhasspy-desktop-satellite."""
import json
from pathlib import Path

from rhasspy_desktop_satellite.config.recorder import RecorderConfig
from rhasspy_desktop_satellite.config.player import PlayerConfig
from rhasspy_desktop_satellite.config.mqtt import MQTTConfig
from rhasspy_desktop_satellite.exceptions import ConfigurationFileNotFoundError


# Default values
DEFAULT_CONFIG = '/etc/rhasspy-desktop-satellite.json'
DEFAULT_SITE = 'default'
DEFAULT_OUTPUT = None
DEFAULT_INPUT = None

# Keys in the JSON configuration file
SITE = 'site'
PLAYER = 'player'
RECORDER = 'recorder'
MQTT = 'mqtt'


# TODO: Define __str__() with explicit settings for debugging.
class ServerConfig:
    """This class represents the configuration of a Hermes audio server.

    Attributes:
        site (str): The site ID of the audio server.
        player (:class:` .PlayerConfig`): Player options
        recorder (:class:` .RecorderConfig`): Recorder options
        mqtt (:class:`.MQTTConfig`): The MQTT options of the configuration.
    """

    def __init__(self, site='default', player=None, recorder=None, mqtt=None):
        """Initialize a :class:`.ServerConfig` object.

        Args:
            site (str): The site ID of the Hermes audio server. Defaults
                to 'default'.
            player (:class:` .PlayerConfig`): Player option settings.
                Defaults to a default :class:`.PlayerConfig` object.
            recorder (:class:` .RecorderConfig`): Recorder option settings.
                Defaults to a default :class:`.RecorderConfig` object.
            mqtt (:class:`.MQTTConfig`, optional): The MQTT connection
                settings. Defaults to a default :class:`.MQTTConfig` object.
        """
        if recorder is None:
            self.recorder = RecorderConfig()
        else:
            self.recorder = recorder

        if player is None:
            self.player = PlayerConfig()
        else:
            self.player = player

        if mqtt is None:
            self.mqtt = MQTTConfig()
        else:
            self.mqtt = mqtt

        self.site = site

    @classmethod
    def from_json_file(cls, filename=None):
        """Initialize a :class:`.ServerConfig` object with settings
        from a JSON file.

        Args:
            filename (str): The filename of a JSON file with the settings.
                Defaults to '/etc/hermes-audio-server'.

        Returns:
            :class:`.ServerConfig`: An object with the settings
            of the Hermes Audio Server.

        The :attr:`mqtt` attribute of the :class:`.ServerConfig`
        object is initialized with the MQTT connection settings from the
        configuration file, or the default values (hostname 'localhost' and
        port number 1883) if the settings are not specified.

        The :attr:`site` attribute of the :class:`.ServerConfig`
        object is initialized with the setting from the configuration file,
        or 'default' is the setting is not specified.

        The :attr:`player` attribute of the :class:`.ServerConfig`
        object is initialized with the Player settings from the configuration file,
        or a default `enabled = false` value if the setting is not specified.

        The :attr:`recorder` attribute of the :class:`.ServerConfig`
        object is initialized with the Recorder settings from the configuration file,
        or a default `enabled = false` value if the setting is not specified.

        Raises:
            :exc:`ConfigurationFileNotFoundError`: If :attr:`filename` doesn't
                exist.

            :exc:`PermissionError`: If we have no read permissions for
                :attr:`filename`.

            :exc:`JSONDecodeError`: If :attr:`filename` doesn't have a valid
                JSON syntax.

        The JSON file should have the following format:

        {
            "site": "default",
            "player": {
                "enabled": true,
                "device": "device name",
                "auto_convert": false,
            },
            "recorder": {
                "enabled": true,
                "device": "device name"
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
        """
        if not filename:
            filename = DEFAULT_CONFIG

        try:
            with Path(filename).open('r') as json_file:
                configuration = json.load(json_file)
        except FileNotFoundError as error:
            raise ConfigurationFileNotFoundError(error.filename)

        return cls(site=configuration.get(SITE, DEFAULT_SITE),
                   player=PlayerConfig.from_json(configuration.get(PLAYER)),
                   recorder=RecorderConfig.from_json(configuration.get(RECORDER)),
                   mqtt=MQTTConfig.from_json(configuration.get(MQTT)))
