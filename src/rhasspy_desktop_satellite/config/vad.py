"""Class for the VAD configuration of rhasspy-desktop-satellite."""

# Default values
DEFAULT_MODE = 1
DEFAULT_SILENCE = 1
DEFAULT_STATUS_MESSAGES = False

# Keys in the JSON configuration file
MODE = 'mode'
SILENCE = 'silence'
STATUS_MESSAGES = 'status_messages'


# TODO: Define __str__() for each class with explicit settings for debugging.
class VADConfig:
    """This class represents the VAD settings for Rhasspy Desktop Satellite.

    Attributes:
        enabled (bool): Whether or not VAD is enabled.
        mode (int): Aggressiveness mode for VAD. 0 is the least aggressive
            about filtering out non-speech, 3 is the most aggressive.
        silence (int): How much silence (no speech detected) in seconds has
            to go by before Rhasspy Desktop Satellite considers it the end of a
            voice message.
        status_messages (bool): Whether or not Rhasspy Desktop Satellite sends
            messages on MQTT when it detects the start or end of a voice
            message.
    """

    def __init__(self, enabled=False, mode=0, silence=2, status_messages=False):
        """Initialize a :class:`.VADConfig` object.

        Args:
            enabled (bool): Whether or not VAD is enabled. Defaults to False.
            mode (int): Aggressiveness mode for VAD. Defaults to 0.
            silence (int): How much silence (no speech detected) in seconds has
                to go by before Rhasspy Desktop Satellite considers it the end of a
                voice message. Defaults to 2.
            status_messages (bool): Whether or not Rhasspy Desktop Satellite sends
                messages on MQTT when it detects the start or end of a voice
                message. Defaults to False.

        All arguments are optional.
        """
        self.enabled = enabled
        self.mode = mode
        self.silence = silence
        self.status_messages = status_messages

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.VADConfig` object with settings from a
        JSON object.

        Args:
            json_object (optional): The JSON object with the VAD settings.
                Defaults to {}.

        Returns:
            :class:`.VADConfig`: An object with the VAD settings.

        The JSON object should have the following format:

        {
            "mode": 0,
            "silence": 2,
            "status_messages": true
        }
        """
        if json_object is None:
            ret = cls(enabled=False)
        else:
            ret = cls(enabled=True,
                      mode=json_object.get(MODE, DEFAULT_MODE),
                      silence=json_object.get(SILENCE, DEFAULT_SILENCE),
                      status_messages=json_object.get(STATUS_MESSAGES,
                                                      DEFAULT_STATUS_MESSAGES))

        return ret
