from __future__ import annotations

class StreamData:
    """
    Store information about stream of data.
    """ 
    def __init__(self, filename, sample_rate, pulses, data):
        """
        Initialize object with associated properties.

        filename: str
            Path to the file with stream data
        sample_rate: int
            Sampling rate of the data
        pulses: np.array
            Numpy array representing the pulses.
        data: np.array
            NumPy array representing all streams of data.
        """
        self.filename = filename
        self.sample_rate = sample_rate
        self.pulses = pulses
        self.data = data