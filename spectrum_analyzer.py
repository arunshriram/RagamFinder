import pyaudio
import struct
import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
matplotlib.use('TkAgg')

# CHUNK = 1024*4
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100

# p = pyaudio.PyAudio()

# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 output=False,
#                 frames_per_buffer=CHUNK)


# fig, ax = plt.subplots()

# x = np.arange(0, 2*CHUNK, 2)
# line, = ax.plot(x, np.random.rand(CHUNK))
# ax.set_xlim(0, CHUNK)
# ax.set_ylim(0, 255)
# while True:
#     data = stream.read(CHUNK, exception_on_overflow=False)
#     data_int = np.array(struct.unpack(str(2 * CHUNK) + 'B', data), dtype='b')[::2] + 127
#     line.set_ydata(data_int)
#     fig.canvas.draw()
#     fig.canvas.flush_events()
#     fig.show()

import scipy.io.wavfile as wavfile
import pylab as pl
rate, data = wavfile.read('440.wav')
t = np.arange(len(data[:,0]))*1.0/rate
pl.plot(t, data[:,0])
pl.show()