"""Classes for the configuration of rhasspy-desktop-satellite."""

# Default values
DEFAULT_DEVICE = None

# Keys in the JSON configuration file
ENABLED = 'enabled'
DEVICE = 'device'
AUTO_CONVERT = 'auto_convert'

# TODO: Define __str__() for each class with explicit settings for debugging.
class PlayerConfig:
    """This class represents the Player settings for Rhasspy Desktop Satellite.

    Attributes:
        enabled (bool): Whether or not the Recorder is enabled.
        device (str): name of the input device to use for the Recorder
        auto_convert (bool): Whether or not the Player should automatically convert
            audio samples in case of unmatched frame rates.
    """

    def __init__(self, enabled=False, device=None, auto_convert=False):
        """Initialize a :class:`.PlayerConfig` object.

        Args:
            enabled (bool): Whether or not Player is enabled. Defaults to False.
            device (str): name of the input device to use for the Recorder.
                Defaults to None.
            auto_convert (bool): Whether or not the Player should automatically convert
                audio samples in case of unmatched frame rates. Defaults to False.

        All arguments are optional.
        """
        self.enabled = enabled
        self.device = device
        self.auto_convert = auto_convert

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.PlayerConfig` object with settings from a
        JSON object.

        Args:
            json_object (optional): The JSON object with the Player settings.
                Defaults to { "enabled": false }.

        Returns:
            :class:`.PlayerConfig`: An object with the Player settings.

        The JSON object should have the following format:

        {
            "enabled": true,
            "device": "device name",
            "auto_convert": false
        }
        """
        if json_object is None:
            ret = cls(enabled=False)
        else:
            ret = cls(enabled=json_object.get(ENABLED, True),
                      device=json_object.get(DEVICE),
                      auto_convert=json_object.get(AUTO_CONVERT, True))

        return ret
