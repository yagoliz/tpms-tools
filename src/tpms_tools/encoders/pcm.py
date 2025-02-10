from typing import List, Tuple


class PCMEncoder:
    def __init__(self, short: int = 1, long: int = 1):
        self.short = short
        self.long = long

    def decode_pcm_signal(self, pulses: List[Tuple[int, int]]) -> List[int]:
        decoded_bits = []

        for pulse, gap in pulses:
            if pulse > 0:
                decoded_bits.extend([1] * (pulse))
            if gap > 0:
                decoded_bits.extend([0] * (gap))

        return decoded_bits

    def encode_pcm_signal(self, bits, s_short=1, s_long=1, verbose=0):
        """
        Encode with PCM: Given a list of bits (1 and 0),
        produce synthetic pulses and gaps which, if decoded with a similar algorithm,
        would yield the original bit sequence.

        Assumes RZ coding (i.e. device.short_width != device.long_width).

        Parameters:
        bits   : List[int] -- a sequence of bits (1 for high, 0 for low)
        device : An object with attributes:
                - sample_rate (in Hz)
                - short_width (in microseconds)
                - long_width  (in microseconds)
                - verbose (optional, integer)
        Returns:
        (pulses, gaps): Tuple[List[int], List[int]]
            pulses : list of pulse durations (in sample units)
            gaps   : list of gap durations (in sample units)
        """
        pulses = []
        gaps = []
        i = 0
        n = len(bits)

        while i < n:
            # Gather consecutive ones (the 'high' part).
            cnt1 = 0
            while i < n and bits[i] == 1:
                cnt1 += 1
                i += 1
            if cnt1 == 0:
                # If the sequence starts with zeros or gaps between events,
                # skip until a high pulse is encountered.
                i += 1
                continue

            # Gather following zeros (the 'low' part).
            cnt0 = 0
            while i < n and bits[i] == 0:
                cnt0 += 1
                i += 1

            # Compute pulse duration.
            # In decoding, ones = round(pulse / s_short).
            pulse_duration = cnt1

            # Compute gap duration.
            # In decoding, zeros = round((gap + s_short - s_long) / s_long)
            # so we reverse that as:
            # gap = zeros * s_long - (s_short - s_long)
            # Note: (s_short - s_long) is negative if device.long_width > device.short_width.
            gap_duration = cnt0 - (s_short - s_long) if cnt0 > 0 else 0

            pulses.append(int(round(pulse_duration)))
            gaps.append(int(round(gap_duration)))

            if verbose > 1:
                print(
                    f"Encoded event: ones={cnt1}, zeros={cnt0}, pulse={pulses[-1]}, gap={gaps[-1]}"
                )

        return list(zip(pulses, gaps))
