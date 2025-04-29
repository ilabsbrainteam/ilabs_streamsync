
from __future__ import annotations

import logging
import os
import pathlib
import subprocess

import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy.io.wavfile import read as wavread
from streamdata import StreamData

FFMPEG_TIMEOUT_SEC = 50

class StreamSync:
    """Synchronize two data streams.

    Inputs: `mne.io.Raw` files, audio files (TODO which formats?),
    and additional camera events.

    Outputs: `mne.Annotations` object created from the camera events and
    time-warped to the timescale of the `Raw`.
    """

    def __init__(self, reference_object, pulse_channel):
        """Initialize StreamSync object with 'Raw' MEG associated with it.
        
        reference_object: str TODO: is str the best method for this, or should this be pathlib obj?
            File path to an MEG raw file with fif formatting. TODO: Verify fif only?
        pulse_channel: str
            A string associated with the stim channel name.
        """
        # Check provided reference_object for type and existence.
        if not reference_object:
            raise TypeError("reference_object is None. Please provide a path.")
        if type(reference_object) is not str:
            raise TypeError("reference_object must be a file path of type str.")
        ref_path_obj = pathlib.Path(reference_object)
        if not ref_path_obj.exists():
            raise OSError("reference_object file path does not exist.")
        if not ref_path_obj.suffix == ".fif":
            raise ValueError("Provided reference object does not point to a .fif file.")

        # Load in raw file if valid
        raw = mne.io.read_raw_fif(reference_object, preload=False, allow_maxshield=True)

        #Check type and value of pulse_channel, and ensure reference object has such a channel.
        if not pulse_channel:
            raise TypeError("pulse_channel is None. Please provide a channel name of type str.")
        if type(pulse_channel) is not str:
            raise TypeError("pulse_chanel parameter must be of type str.")
        if raw[pulse_channel] is None:
            raise ValueError('pulse_channel does not exist in refrence_object.')
        

        self.raw = mne.io.read_raw_fif(reference_object, preload=False, allow_maxshield=True)
        self.ref_stream = raw[pulse_channel]

        self.sfreq = self.raw.info["sfreq"]  # Hz

        self.streams = [] # list of StreamData objects

    def add_stream(self, stream, channel=None, events=None):
        """Add a new ``Raw`` or video stream, optionally with events.

        stream : str
            File path to an audio or FIF stream.
        channel : str | int | None
            Which channel of `stream` contains the sync pulse sequence.
        events : array-like | None
            Events associated with the stream. TODO: should they be integer sample
            numbers? Timestamps? Do we support both?
        """
        self.streams.append(self._extract_data_from_stream(stream, channel=channel))

    def _extract_data_from_stream(self, stream, channel):
        """Extract pulses and raw data from stream provided. TODO: Implement adding a annotation stream."""
        ext = pathlib.Path(stream).suffix
        if ext == ".wav":
            return self._extract_data_from_wav(stream, channel)
        raise TypeError("Stream provided was of unsupported format. Please provide a wav file.")


    def _extract_data_from_wav(self, stream, channel):
        """Return tuple of (pulse channel, audio channel) from stereo file."""
        srate, wav_signal = wavread(stream)
        return StreamData(filename = stream, sample_rate=srate, pulses=wav_signal[:,channel], data=wav_signal[:,1-channel])

    def remove_stream(self, stream):
        pass

    def do_syncing(self):
        """Synchronize all streams with the reference stream."""
        # TODO (waves hands) do the hard part.
        # TODO spit out a report of correlation/association between all pairs of streams

    def plot_sync_pulses(self, tmin=0, tmax=None):
        """Plot each stream in the class.
        
        tmin: int
            Minimum timestamp to be graphed.
        tmax: int
            Maximum timestamp to be graphed.    
        """
        fig, axset = plt.subplots(len(self.streams)+1, 1, figsize = [8,6]) #show individual channels seperately, and the 0th plot is the combination of these. 
        # Plot reference_object
        trig, tt_trig = self.ref_stream
        trig = trig.reshape(tt_trig.shape)
        idx = np.where((tt_trig>=tmin) & (tt_trig<tmax))
        axset[0].plot(tt_trig[idx], trig[idx]*100, c='r')
        axset[0].set_title("Reference MEG")
        # Plot all other streams
        for i, stream in enumerate(self.streams):
            npts = len(stream.pulses)
            tt = np.arange(npts) / stream.sample_rate
            idx = np.where((tt>=tmin) & (tt<tmax))
            axset[i+1].plot(tt[idx], stream.pulses[idx].T)
            axset[i+1].set_title(pathlib.Path(stream.filename).name)
            # Make label equal to simply the cam number
        plt.show()

def extract_audio_from_video(path_to_video, output_dir, overwrite=False):
    """Extract audio from path provided.

    path_to_video: str
        Path to audio file
        TODO allow path_to_video to take regex?
    output_dir: str
        Path to directory where extracted audio should be sent

    Effects:
        Creates output directory if non-existent. For each video found, creates
        a file with the associated audio labeled the same way.

    Raises:
        ValueException if video path does not exist, 
        Exception if filename is taken in output_dir
    """
    p = pathlib.Path(path_to_video)
    audio_file = p.with_stem(f"{p.stem}_16_bit").with_suffix(".wav").name
    if not p.exists():
        raise ValueError('Path provided cannot be found.')
    if not overwrite and pathlib.PurePath.joinpath(pathlib.Path(output_dir), pathlib.Path(audio_file)).exists():
        raise Exception(f"Audio already exists for {path_to_video} in output directory.")
    
    # Create output directory is non-existent.
    od = pathlib.Path(output_dir)
    od.mkdir(exist_ok=True, parents=True)
    output_path = output_dir + "/" + audio_file

    command = ['ffmpeg',
        '-acodec', 'pcm_s24le',       # force little-endian format (req'd for Linux)
        '-i', path_to_video,
        '-map', '0:a',                # audio only (per DM)
#         '-af', 'highpass=f=0.1',
        '-acodec', 'pcm_s16le',
        '-ac', '2',                   # no longer mono output, so setting to "2"
        '-y', '-vn',                  # overwrite output file without asking; no video
        '-loglevel', 'error',
        output_path]
    pipe = subprocess.run(command, timeout=FFMPEG_TIMEOUT_SEC, check=False)

    logger = logging.getLogger(__name__)
    if pipe.returncode==0:
        logger.info(f'Audio extraction was successful for {path_to_video}')
    else:
        logger.info(f"Audio extraction unsuccessful for {path_to_video}")