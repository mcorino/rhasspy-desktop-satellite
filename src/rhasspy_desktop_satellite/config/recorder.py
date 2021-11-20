"""Classes for the configuration of rhasspy-desktop-satellite."""

from rhasspy_desktop_satellite.config.vad import VADConfig

# Default values
DEFAULT_DEVICE = None
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_SAMPLE_WIDTH = 2
DEFAULT_CHANNELS = 1

# Keys in the JSON configuration file
ENABLED = 'enabled'
DEVICE = 'device'
WAKEUP = 'wakeup'
SAMPLE_RATE = 'sampleRate'
SAMPLE_WIDTH = 'sampleWidth'
CHANNELS = 'channels'
VAD = 'vad'

# TODO: Define __str__() for each class with explicit settings for debugging.
class RecorderConfig:
    """This class represents the Recorder settings for Rhasspy Desktop Satellite.

    Attributes:
        enabled (bool): Whether or not the Recorder is enabled.
        device (str): name of the input device to use for the Recorder
        wakeup (bool): Whether or not to record for wake word detection.
        sample_rate (int): Sample rate for recording
        sample_width (int): Sample width for recording
        channels (int): Channels for recording
        vad (:class:`.VADConfig`): The VAD options of the configuration.
    """

    def __init__(self, enabled=False, device=None, wakeup=False, sample_rate=None, sample_width=None, channels=None, vad=None):
        """Initialize a :class:`.RecorderConfig` object.

        Args:
            enabled (bool): Whether or not Recorder is enabled. Defaults to False.
            device (str): name of the input device to use for the Recorder.
                Defaults to None.
            wakeup (bool): Whether or not to record for wake word detection.
                Defaults to False.
            sample_rate (int): Sample rate for recording.
                Defaults to 16000.
            sample_width (int): Sample width for recording.
                Defaults to 2.
            channels (int): Channels for recording
                Defaults to 1.
            vad (:class:`.VADConfig`, optional): The VAD settings. Defaults
                to a default :class:`.VADConfig` object, which disables voice
                activity detection.

        All arguments are optional.
        """
        self.enabled = enabled
        self.device = device
        self.wakeup = wakeup
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.channels = channels

        if vad is None:
            self.vad = VADConfig()
        else:
            self.vad = vad

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.RecorderConfig` object with settings from a
        JSON object.

        Args:
            json_object (optional): The JSON object with the Recorder settings.
                Defaults to { "enabled": false }.

        Returns:
            :class:`.RecorderConfig`: An object with the Recorder settings.

        The :attr:`vad` attribute of the :class:`.RecorderConfig` object is
        initialized with the settings from the configuration file, or not
        enabled when not specified. The VADConfig is only effectively used
        when the :attr:`wakeup` attribute is true.

        The JSON object should have the following format:

        {
            "enabled": true,
            "device": "device name",
            "wakeup": False,
            "sampleRate": 16000,
            "sampleWidth": 2,
            "channels": 1,
            "vad": {
                "mode": 0,
                "silence": 2,
                "status_messages": true
            }
        }
        """
        if json_object is None:
            ret = cls(enabled=False)
        else:
            ret = cls(enabled=json_object.get(ENABLED, True),
                      device=json_object.get(DEVICE, DEFAULT_DEVICE),
                      wakeup=json_object.get(WAKEUP, False),
                      sample_rate=json_object.get(SAMPLE_RATE, DEFAULT_SAMPLE_RATE),
                      sample_width=json_object.get(SAMPLE_WIDTH, DEFAULT_SAMPLE_WIDTH),
                      channels=json_object.get(CHANNELS, DEFAULT_CHANNELS),
                      vad=VADConfig.from_json(json_object.get(VAD)))

        return ret
