"""This module contains exceptions defined for Rhasspy Desktop Satellite."""


class RDSatelliteServerError(Exception):
    """Base class for exceptions raised by Rhasspy Desktop Satellite code.

    By catching this exception type, you catch all exceptions that are
    defined by the Hermes Audio Server code."""


class ConfigurationFileNotFoundError(RDSatelliteServerError):
    """Raised when the configuration file is not found."""

    def __init__(self, filename):
        """Initialize the exception with a string representing the filename."""
        self.filename = filename


class NoDefaultAudioDeviceError(RDSatelliteServerError):
    """Raised when there's no default audio device available."""

    def __init__(self, inout):
        """Initialize the exception with a string representing input or output.
        """
        self.inout = inout


class UnsupportedPlatformError(RDSatelliteServerError):
    """Raised when the platform Rhasspy Desktop Satellite is running on is not
    supported."""

    def __init__(self, platform):
        """Initialize the exception with a string representing the platform."""
        self.platform = platform
