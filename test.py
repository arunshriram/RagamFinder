#! /usr/bin/env python

import sys, os
from aubio import source, pitch
import os.path
from numpy import array, ma
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile 
import peakutils 
from math import log2, pow
from RagamDB import *

def freqToPitch(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    return name[n] #+ str(octave)

# Takes a list of pitch frequencies from FFT analysis, and returns a list of the fundamental frequencies found.
def getFundamentalFrequencies(pitchFrequencies):
    if len(pitchFrequencies) < 0:
        return []
    if len(pitchFrequencies) == 1:
        return pitchFrequencies 
    funFreqs = []
    for freq in pitchFrequencies:
        if funFreqs == []:
            funFreqs.append(freq)
        else:
            for i in range(1, 9):
                pass
            
def showPlotForSample(rate, samples):
        # plt.figure(1)
        # plt.xlabel('time')
        # plt.ylabel('amplitude')
        # plt.plot(samples)
        # plt.show()
        len_data = len(samples)

        channel_1 = np.zeros(2**(int(np.ceil(np.log2(len_data)))))
        channel_1[0:len_data] = samples

        fourier = np.fft.fft(channel_1)
        w = np.linspace(0, 44100, len(fourier))

        # First half is the real component, second half is imaginary
        fourier_to_plot = abs(fourier[0:len(fourier)//2])
        w = w[0:len(fourier)//2]

        indexesOfPeaks = peakutils.indexes(fourier_to_plot, thres=0.07)
        peakFrequencies = [w[u] for u in indexesOfPeaks]
        
        print(getFundamentalFrequencies(peakFrequencies))
        xxx = peakutils.interpolate(w, fourier_to_plot, ind=indexesOfPeaks)
        pitchPeaks = [freqToPitch(freq) for freq in peakFrequencies]
        print(peakFrequencies)
        # print("XXX: %s" % str([freqToPitch(freq) for freq in xxx]))
        # print("Peak Frequencies: %s" % str(pitchPeaks))
        # print()
        plt.figure(1)
        plt.xlabel('frequency')
        plt.ylabel('amplitude')
        plt.plot(w[:int(len(w)/10)], fourier_to_plot[:int(len(fourier_to_plot)/10)])
        plt.show()
        return pitchPeaks

def processFile(filename):
    
    downsample = 1
    samplerate = 44100 // downsample
    if len( sys.argv ) > 2: samplerate = int(sys.argv[2])

    win_s = 4096 // downsample # fft size
    hop_s = 512  // downsample # hop size

    s = source(filename, samplerate, win_s)
    samplerate = s.samplerate

        
    # total number of frames read
    total_frames = 0
    count = 0

    mostFrequentPitches = {}

    while True:
        samples, read = s()
        frequentPitches = showPlotForSample(44100, samples)
        for pitch in frequentPitches:
            if pitch not in mostFrequentPitches:
                mostFrequentPitches[pitch] = 0
            else:
                mostFrequentPitches[pitch] += 1
        total_frames += read
        print(read)
        print(hop_s)
        if read < hop_s: break
        count += 1

    # print("Count: ", count)
    # print("Total frames: ", total_frames)
    # print(mostFrequentPitches)
    return sorted(mostFrequentPitches.items(), reverse=True, key = lambda kv: (kv[1], kv[0]))

def main():
    arohanam = [Note("S"), Note("M", 1), Note("P"), Note("S")]
    avarohanam = [Note("S"), Note("P"), Note("M", 1), Note("S")]
    ragdb = RagamDB("full-ragam-list.txt")
    print(ragdb.searchByScales(arohanam, avarohanam))
    # print()
    # print("Beginning sruthi analysis...")
    # print()
    # successTracker = {}
    # count = 1
    # file = "small_test_3.mp3"
    # pitches = processFile(file)
    # print(pitches)
    
    # for filenam in os.listdir("TestData"):
    #     if(not (filenam.endswith("mp3") or filenam.endswith("m4a") or filenam.endswith("wav"))):
    #         continue
    #     file_to_process = "TestData/" + filenam
        
    #     file = filenam.split('.')[0]
    #     print("%d. Verifying %s......" % (count, file), end="")
    #     pitches = processFile(file_to_process)
    #     print(pitches)
    #     if(pitches[0][0] == file.split("_")[0]):
    #         print("Success")
    #         successTracker[filenam] = "Success"
    #     else:
    #         print("Failure! Found %s instead." % pitches[0][0])
    #         successTracker[filenam] = "...Failure"
            
    #     print('\n')
    #     count += 1
    # # audioAnalyzer.plotPitches()

    # # Print brief summary report
    # count = 1
    # print()
    # successes = 0
    # total = 0
    # for item in successTracker:
    #     print("%d. %s\t.....%s" % (count, item, successTracker[item]))
    #     if successTracker[item] == "Success":
    #         successes += 1
    #     total += 1
    #     count += 1
    # print()
    # print("Success rate: %s%%" % ('{0:.2f}'.format(100*(successes/float(total)))))
    
if __name__ == '__main__':
    main()