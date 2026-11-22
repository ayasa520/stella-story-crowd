def read_pcm(path, start=0, end=None):
    with wave.open(str(path)) as stream:
        layout = dict(channels=stream.getnchannels(), sampleBytes=stream.getsampwidth(),
                      rate=stream.getframerate(), frames=stream.getnframes())
        assert layout['channels'] == 1 and layout['sampleBytes'] == 2
        left = round(start * layout['rate'])
        right = layout['frames'] if end is None else round(end * layout['rate'])
        stream.setpos(left)
        pcm = np.frombuffer(stream.readframes(right-left), '<i2').astype(np.float64)/32768
        assert len(pcm) == right-left
    return pcm, layout

def to_4k(pcm, original_rate):
    assert original_rate in (32000, 48000) and original_rate % RATE == 0
    # Match the earlier independent Julius check: symmetric compensated
    # low-pass filtering followed by exact integer decimation preserves cue0.
    positions = np.arange(-64, 65)
    kernel = (2*1800/original_rate * np.sinc(2*1800/original_rate*positions)
              * np.hamming(129))
    kernel /= kernel.sum()
    return np.convolve(pcm, kernel, mode='same')[::original_rate//RATE]

def measure(label, template, cue_offset=0):
        template = template.copy()
        template -= template.mean()
        query = compute.query(template, float(np.dot(template, template)))
        scores = compute.scores(signal, query)
        values = []
        for at, score in compute.peaks(scores.copy(), 5, 0, round(.4*RATE)):
            block = source[at:at+len(template)]
            centered = block-block.mean()
            signed = float(np.dot(centered, template)/np.sqrt(np.dot(centered, centered)*query.energy))
            values.append(dict(cueZeroPcmSeconds=WINDOW[0]+at/RATE-cue_offset,
                               templateStartPcmSeconds=WINDOW[0]+at/RATE,
                               absoluteNcc=score, signedNcc=signed))
        item = dict(label=label, templateStartInCueSeconds=cue_offset,
                    templateDuration=len(template)/RATE, peaks=values)
        comparisons.append(item)
        return item
