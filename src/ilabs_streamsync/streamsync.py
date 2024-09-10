
from __future__ import annotations

import os
import pathlib
import subprocess

import logger
import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy.io.wavfile import read as wavread

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
            raise TypeError("reference_object is None. Please provide reference_object of type str.")
        if type(reference_object) is not str:
            raise TypeError("reference_object must be a file path of type str.")
        ref_path_obj = pathlib.Path(reference_object)
        if not ref_path_obj.exists():
            raise OSError("reference_object file path does not exist.")
        if not ref_path_obj.suffix == ".fif":
            raise ValueError("Provided reference object is not of type .fif")

        # Load in raw file if valid
        raw = mne.io.read_raw_fif(reference_object, preload=False, allow_maxshield=True)

        #Check type and value of pulse_channel, and ensure reference object has such a channel.
        if not pulse_channel:
            raise TypeError("pulse_channel is None. Please provide pulse_chanel parameter of type int.")
        if type(pulse_channel) is not str:
            raise TypeError("pulse_chanel parameter must be of type str.")
        if raw[pulse_channel] is None:
            raise ValueError('pulse_channel does not exist in refrence_object.')
        

        self.raw = mne.io.read_raw_fif(reference_object, preload=False, allow_maxshield=True)
        self.ref_stream = raw[pulse_channel]
        self.sfreq = self.raw.info["sfreq"]  # Hz

        self.streams = [] # of (filename, srate, Pulses, Data)

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
        srate, pulses, data = self._extract_data_from_stream(stream, channel=channel)
        self.streams.append((stream, srate, pulses, data))

    def _extract_data_from_stream(self, stream, channel):
        """Extract pulses and raw data from stream provided."""
        ext = pathlib.Path(stream).suffix
        if ext == ".wav":
            return self._extract_data_from_wav(stream, channel)
        raise TypeError("Stream provided was of unsupported format. Please provide a wav file.")


    def _extract_data_from_wav(self, stream, channel):
        """Return tuple of (pulse channel, audio channel) from stereo file."""
        srate, wav_signal = wavread(stream)
        return (srate, wav_signal[:,channel], wav_signal[:,1-channel])

    def do_syncing(self):
        """Synchronize all streams with the reference stream."""
        # TODO (waves hands) do the hard part.
        # TODO spit out a report of correlation/association between all pairs of streams

    def plot_sync_pulses(self, tmin=0, tmax=float('inf')):
        """Plot each stream in the class."""
        # TODO Plot the raw file on the first plot.
        fig, axset = plt.subplots(len(self.streams)+1, 1, figsize = [8,6]) #show individual channels seperately, and the 0th plot is the combination of these. 
        for i, stream in enumerate(self.streams):
            npts = len(stream[2])
            tt = np.arange(npts) / stream[1]
            idx = np.where((tt>=tmin) & (tt<tmax))
            axset[i+1].plot(tt[idx], stream[2][idx].T)
            axset[i+1].set_title(pathlib.Path(stream[0]).name)
            # Make label equal to simply the cam number
        plt.show()

def extract_audio_from_video(path_to_video, output_dir):
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
    audio_codecout = 'pcm_s16le'
    audio_suffix = '_16bit'
    p = pathlib.Path(path_to_video)
    audio_file = p.stem + audio_suffix + '.wav'
    if not p.exists():
        raise ValueError('Path provided cannot be found.')
    if pathlib.PurePath.joinpath(pathlib.Path(output_dir), pathlib.Path(audio_file)).exists():
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
        '-acodec', audio_codecout,
        '-ac', '2',                   # no longer mono output, so setting to "2"
        '-y', '-vn',                  # overwrite output file without asking; no video
        '-loglevel', 'error',
        output_path]
    pipe = subprocess.run(command, timeout=FFMPEG_TIMEOUT_SEC, check=False)

    if pipe.returncode==0:
        print(f'Audio extraction was successful for {path_to_video}')
    else:
        print(f"Audio extraction unsuccessful for {path_to_video}")