import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.io import wavfile # get the api
import numpy as np

fs, data = wavfile.read('c4toa4.wav') # load the data
c = fft(data) # calculate fourier transform (complex numbers list)
d = int(len(c)/2)  # you only need half of the fft list (real signal symmetry)
k = np.arange((len(data)/2) - 1)
T = ((len(data)/2) - 1)/fs
frqLabel = k/T
plt.xlabel('Frequency')
plt.plot(frqLabel, abs(c[:(d-1)]),'r') 
plt.show()