"""Module with the Satellite server class."""
import io
import json
import queue
from threading import Thread, Condition, Lock
import wave
from queue import Queue
import time
from humanfriendly import format_size

import audioop

from rhasspy_desktop_satellite.exceptions import NoDefaultAudioDeviceError
from rhasspy_desktop_satellite.mqtt import MQTTClient

AUDIO_FRAME = 'hermes/audioServer/{}/audioFrame'
CHUNK_SIZE = 2048

ASR_START_LISTENING = 'hermes/asr/startListening'
ASR_STOP_LISTENING = 'hermes/asr/stopListening'
ASR_TOGGLE_OFF = 'hermes/asr/toggleOff'

HOTWORD_TOGGLE_ON = 'hermes/hotword/toggleOn'
HOTWORD_TOGGLE_OFF = 'hermes/hotword/toggleOff'

PLAY_BYTES = 'hermes/audioServer/{}/playBytes/+'
PLAY_FINISHED = 'hermes/audioServer/{}/playFinished'


# TODO: Call stream.stop_stream() and stream.close()
class SatelliteServer(MQTTClient):
    """This class creates an MQTT client that acts as an audio recorder AND player for the
    Hermes protocol.
    """

    def initialize(self):
        """Initialize a Rhasspy Desktop Satellite server."""
        self.logger.debug('Probing for available audio devices...')
        self.recorder_enabled = self.config.recorder.enabled
        self.audio_in = None
        self.audio_in_index = -1
        self.player_enabled = self.config.player.enabled
        self.audio_out = None
        self.audio_out_index = -1
        for index in range(self.audio.get_device_count()):
            device = self.audio.get_device_info_by_index(index)
            name = device['name']
            channels = device['maxInputChannels']
            if channels:
                self.logger.debug('[%d] %s (%d)', index, name, int(device['defaultSampleRate']))
            if self.recorder_enabled and (name == self.config.recorder.device):
                self.audio_in_index = index
                self.audio_in = name
            if self.player_enabled and (name == self.config.player.device):
                self.audio_out_index = index
                self.audio_out = name
                self.audio_out_rate = int(device['defaultSampleRate'])
        if self.recorder_enabled and (self.audio_in_index < 0):
            if not self.config.recorder.device is None:
                self.logger.warning('Could not connect to audio input %s.', self.config.recorder.device)
            try:
                self.audio_in = self.audio.get_default_input_device_info()['name']
            except OSError:
                raise NoDefaultAudioDeviceError('input')
        self.logger.info('Connected to audio input %s.', self.audio_in)
        if self.player_enabled and (self.audio_out_index < 0):
            if not self.config.player.device is None:
                self.logger.warning('Could not connect to audio output %s.', self.config.player.device)
            try:
                self.audio_out = self.audio.get_default_output_device_info()['name']
                self.audio_out_rate = int(self.audio.get_default_output_device_info()['defaultSampleRate'])
            except OSError:
                raise NoDefaultAudioDeviceError('output')
        self.logger.info('Connected to audio output %s.', self.audio_out)

        self.lock = Lock()
        self.cv = Condition(self.lock)
        self.listen_audio = False
        self.chunk_queue: Queue = Queue()
        self.chunk_size = CHUNK_SIZE

        # Frames to skip between audio summaries
        self.summary_skip_frames = 5
        self.summary_frames_left = self.summary_skip_frames

        self.wakeword_listen = self.recorder_enabled and self.config.recorder.wakeup
        if self.wakeword_listen:
            self.logger.info('Wakeword listening enabled for site %s.', self.config.site)

        self.player_enabled = self.config.player.enabled
        self.playing_audio = False

        self.server_stop = False

        self.record_audio = self.wakeword_listen

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the audio player connects to the MQTT
        broker."""
        super().on_connect(client, userdata, flags, result_code)
        # Listen to the MQTT topic defined in the Hermes protocol to play a WAV
        # file.
        # See https://docs.snips.ai/reference/hermes#playing-a-wav-sound
        if self.recorder_enabled:
            self.mqtt.subscribe(ASR_TOGGLE_OFF)
            self.mqtt.message_callback_add(ASR_TOGGLE_OFF, self.on_stop_listening)
            self.logger.info('Subscribed to %s topic.', ASR_TOGGLE_OFF)
            self.mqtt.subscribe(ASR_START_LISTENING)
            self.mqtt.message_callback_add(ASR_START_LISTENING, self.on_start_listening)
            self.logger.info('Subscribed to %s topic.', ASR_START_LISTENING)
            self.mqtt.subscribe(ASR_STOP_LISTENING)
            self.mqtt.message_callback_add(ASR_STOP_LISTENING, self.on_stop_listening)
            self.logger.info('Subscribed to %s topic.', ASR_STOP_LISTENING)

        if self.recorder_enabled and self.config.recorder.wakeup:
            self.mqtt.subscribe(HOTWORD_TOGGLE_ON)
            self.mqtt.message_callback_add(HOTWORD_TOGGLE_ON, self.on_hotword_on)
            self.logger.info('Subscribed to %s topic.', HOTWORD_TOGGLE_ON)
            self.mqtt.subscribe(HOTWORD_TOGGLE_OFF)
            self.mqtt.message_callback_add(HOTWORD_TOGGLE_OFF, self.on_hotword_off)
            self.logger.info('Subscribed to %s topic.', HOTWORD_TOGGLE_OFF)

        if self.recorder_enabled and not self.player_enabled:
            play_finished = PLAY_FINISHED.format(self.config.site)
            self.mqtt.subscribe(play_finished)
            self.mqtt.message_callback_add(play_finished, self.on_play_finished)
            self.logger.info('Subscribed to %s topic.', play_finished)

        if self.recorder_enabled or self.player_enabled:
            play_bytes = PLAY_BYTES.format(self.config.site)
            self.mqtt.subscribe(play_bytes)
            self.mqtt.message_callback_add(play_bytes, self.on_play_bytes)
            self.logger.info('Subscribed to %s topic.', play_bytes)

    def on_play_finished(self, client, userdata, message):
        """Callback that is called when the audio player receives a PLAY_FINISHED
        message on MQTT.
        """
        self.logger.info('Received a %s message'
                         ' on site %s.',
                         message.topic,
                         self.config.site)

        with self.cv:
            self.play_audio = False
            self.record_audio = self.listen_audio
            self.cv.notify_all()

    def on_hotword_on(self, client, userdata, message):
        """Callback that is called when the audio player receives a HOTWORD_TOGGLE_ON
        message on MQTT.
        """
        msgdata = json.loads(message.payload)
        if msgdata.get('siteId', '') == self.config.site:
            self.logger.info('Received a %s message'
                             ' on site %s.',
                             message.topic,
                             self.config.site)
            with self.cv:
                self.wakeword_listen = True
                self.record_audio = not self.play_audio
                self.cv.notify_all()

    def on_hotword_off(self, client, userdata, message):
        """Callback that is called when the audio player receives a HOTWORD_TOGGLE_OFF
        message on MQTT.
        """
        msgdata = json.loads(message.payload)
        if msgdata.get('siteId', '') == self.config.site:
            self.logger.info('Received a %s message'
                             ' on site %s.',
                             message.topic,
                             self.config.site)
            with self.cv:
                self.wakeword_listen = False
                self.record_audio = self.listen_audio and not self.play_audio
                self.cv.notify_all()

    def on_start_listening(self, client, userdata, message):
        """Callback that is called when the audio player receives a ASR_START_LISTENING
        message on MQTT.
        """
        msgdata = json.loads(message.payload)
        if msgdata.get('siteId', '') == self.config.site:
            self.logger.info('Received a %s message'
                             ' on site %s.',
                             message.topic,
                             self.config.site)
            with self.cv:
                self.listen_audio = True
                self.record_audio = not self.play_audio
                self.cv.notify_all()

    def on_stop_listening(self, client, userdata, message):
        """Callback that is called when the audio player receives a ASR_STOP_LISTENING
        or ASR_TOGGLE_OFF message on MQTT.
        """
        msgdata = json.loads(message.payload)
        if msgdata.get('siteId', '') == self.config.site:
            self.logger.info('Received a %s message'
                             ' on site %s.',
                             message.topic,
                             self.config.site)
            with self.cv:
                self.listen_audio = False
                self.record_audio = self.wakeword_listen and not self.play_audio
                self.cv.notify_all()

    def start(self):
        """Start the event loop to the MQTT broker and start the audio
        threads."""
        self.logger.debug('Starting server threads...')
        if self.recorder_enabled:
            Thread(target=self.record, daemon=True).start()
            Thread(target=self.publish_chunks, daemon=True).start()
        super().start()

    def stop(self):
        with self.cv:
            self.record_audio = False
            self.server_stop = True
            self.cv.notify_all()
        super().stop()

    def publish_frames(self, frames):
        """Publish frames on MQTT."""
        audio_frame_topic = AUDIO_FRAME.format(self.config.site)
        audio_frame_message = frames.getvalue()
        self.mqtt.publish(audio_frame_topic, audio_frame_message)
        self.logger.debug('Published message on MQTT topic:')
        self.logger.debug('Topic: %s', audio_frame_topic)
        self.logger.debug('Message: %d bytes', len(audio_frame_message))

    def record(self):
        """Record audio."""
        while not self.server_stop:
            if self.record_audio:
                try:
                    self.logger.debug('Opening audio input stream...')
                    if self.audio_in_index < 0:
                        stream = self.audio.open(format=self.audio.get_format_from_width(self.config.recorder.sample_width),
                                                 channels=self.config.recorder.channels,
                                                 rate=self.config.recorder.sample_rate,
                                                 input=True,
                                                 frames_per_buffer=CHUNK_SIZE)
                    else:
                        stream = self.audio.open(format=self.audio.get_format_from_width(self.config.recorder.sample_width),
                                                 channels=self.config.recorder.channels,
                                                 rate=self.config.recorder.sample_rate,
                                                 input=True,
                                                 input_device_index=self.audio_in_index,
                                                 frames_per_buffer=CHUNK_SIZE)

                    self.logger.info('Starting broadcasting audio from device %s'
                                     ' on site %s...', self.audio_in, self.config.site)

                    try:
                        while self.record_audio:
                            # prevent blocking reads as much as possible
                            num_avail = stream.get_read_available()
                            if num_avail > 0:
                                frames = stream.read(num_frames=CHUNK_SIZE if num_avail > CHUNK_SIZE else num_avail,
                                                     exception_on_overflow=False)
                            else:
                                frames = None
                            # if still recording publish the frames
                            if self.record_audio:
                                if frames:
                                    self.chunk_queue.put(frames)
                                else:
                                    # Avoid 100% CPU usage
                                    time.sleep(0.01)
                    except Exception as ee:
                        self.logger.exception("record")
                        self.logger.error('Reading Audio chunks Error for % : %s',
                                          self.config.site,
                                          str(ee))

                    stream.stop_stream()
                    stream.close()

                    self.logger.info('Finished broadcasting audio from device %s'
                                     ' on site %s.', self.audio_in, self.config.site)

                except Exception as e:
                    self.logger.exception("record")
                    self.logger.error('Recording Error for % : %s',
                                      self.config.site,
                                      str(e))

            if not self.record_audio:
                with self.cv:
                    self.cv.wait()

    def publish_chunks(self):
        """Publish audio chunks to MQTT."""
        try:
            while not self.server_stop:
                try:
                    chunk = self.chunk_queue.get(timeout=0.1)
                    if chunk:
                        # MQTT output
                        with io.BytesIO() as wav_buffer:
                            with wave.open(wav_buffer, 'wb') as wav:
                                # pylint: disable=no-member
                                wav.setframerate(self.config.recorder.sample_rate)
                                wav.setsampwidth(self.config.recorder.sample_width)
                                wav.setnchannels(self.config.recorder.channels)
                                wav.writeframes(chunk)

                            self.publish_frames(wav_buffer)
                except queue.Empty:
                    # self.logger.debug('Chunk queue empty')
                    pass

        except Exception as e:
            self.logger.exception("publish_chunks")
            self.logger.error('Publishing chunks Error for %s : %s',
                              self.config.site,
                              str(e))

    def on_play_bytes(self, client, userdata, message):
        """Callback that is called when the audio player receives a PLAY_BYTES
        message on MQTT.
        """
        with self.lock:
            self.play_audio = True
            self.record_audio = False

        if self.player_enabled:
            request_id = message.topic.split('/')[4]
            length = format_size(len(message.payload), binary=True)
            self.logger.info('Received an audio message of length %s'
                             ' with request id %s on site %s.',
                             length,
                             request_id,
                             self.config.site)

            with io.BytesIO(message.payload) as wav_buffer:
                try:
                    with wave.open(wav_buffer, 'rb') as wav:
                        sample_width = wav.getsampwidth()
                        sample_format = self.audio.get_format_from_width(sample_width)
                        n_channels = wav.getnchannels()
                        frame_rate = wav.getframerate()

                        self.logger.debug('Sample width: %s', sample_width)
                        self.logger.debug('Channels: %s', n_channels)
                        self.logger.debug('Frame rate: %s', frame_rate)

                        self.logger.debug('Opening audio output stream...')
                        audio_out_rate = self.audio_out_rate
                        if self.audio_out_index < 0:
                            stream = self.audio.open(format=sample_format,
                                                     channels=n_channels,
                                                     rate=frame_rate,
                                                     output=True)
                            audio_out_rate = frame_rate
                        else:
                            stream = self.audio.open(format=sample_format,
                                                     channels=n_channels,
                                                     rate=self.audio_out_rate,
                                                     output_device_index=self.audio_out_index,
                                                     output=True)

                        self.logger.debug('Playing WAV buffer on audio output...')
                        data = wav.readframes(CHUNK_SIZE)

                        state = None
                        while data:
                            if self.config.player.auto_convert and (frame_rate != audio_out_rate):
                                self.logger.debug("Converting frame rate from %d to %d", frame_rate, self.audio_out_rate)
                                outdata, state = audioop.ratecv(data, sample_width, n_channels, frame_rate,
                                                                self.audio_out_rate, state)
                            else:
                                outdata = data
                            stream.write(outdata)
                            data = wav.readframes(CHUNK_SIZE)

                        stream.stop_stream()
                        self.logger.debug('Closing audio output stream...')
                        stream.close()

                        with self.cv:
                            self.play_audio = False
                            self.record_audio = self.listen_audio
                            self.cv.notify_all()

                        self.logger.info('Finished playing audio message with id %s'
                                         ' on device %s on site %s.',
                                         request_id,
                                         self.audio_out,
                                         self.config.site)

                        # Publish a message that the audio service has finished
                        # playing the sound.
                        # See https://docs.snips.ai/reference/hermes#being-notified-when-sound-has-finished-playing
                        # This implementation doesn't publish a session ID.
                        play_finished_topic = PLAY_FINISHED.format(self.config.site)
                        play_finished_message = json.dumps({'id': request_id,
                                                            'siteId': self.config.site})
                        self.mqtt.publish(play_finished_topic,
                                          play_finished_message)
                        self.logger.debug('Published message on MQTT topic:')
                        self.logger.debug('Topic: %s', play_finished_topic)
                        self.logger.debug('Message: %s', play_finished_message)
                except wave.Error as error:
                    self.logger.warning('%s', str(error))
                except EOFError:
                    self.logger.warning('End of WAV buffer')
