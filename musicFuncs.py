# Author: Arun Shriram
# This file holds a few auxilary functions that handle converting frequencies to pitches, and pitches
# to notes. These utility functions are used for fundamental frequency analysis and note extraction.

from math import log2, pow
import numpy as np
from RagamDB import *
import peakutils, os
from numpy import array, ma
import matplotlib.pyplot as plt


# Returns the number of steps between a start pitch and end pitch.
# The number of steps is positive if the end pitch is higher than the starting pitch. Negative if otherwise. 0 if the same frequency.
def getNumSteps(start, end):
    startPitch = start[:len(start) - 1]
    startClass = int(start[len(start)-1:])
    endPitch = end[:len(end) - 1]
    endClass = int(end[len(end) - 1:])
    pitchList = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    steps = 0
    if endClass == startClass:
        steps = abs(pitchList.index(endPitch) - pitchList.index(startPitch))
    elif endClass > startClass:
        steps += pitchList.index("B") - pitchList.index(startPitch)
        startClass += 1
        while startClass != endClass:
            steps += 12
            startClass += 1
        steps += pitchList.index(endPitch) + 1
    elif endClass < startClass:
        steps += pitchList.index(startPitch) - pitchList.index("C") + 1
        startClass -= 1
        while startClass != endClass:
            steps += 12
            startClass -=1
        steps += pitchList.index("B") - pitchList.index(endPitch)
        steps *= -1
    return steps

# Given a number of steps, assuming numSteps = 0 represents S, return the corresponding note.
# Assume numSteps will always be an integer from 0-11.
def convertPitchFromSteps(numSteps):
    octave = 1
    if numSteps >= 12:
        octave = 2
    elif numSteps <= -12:
        octave = 0
    numSteps %= 12
    if numSteps == 0:
        return Note(note="S", octave=octave)
    elif abs(numSteps) == 12:
        if numSteps == 12:
            return Note(note="S", octave=octave)
        else:
            return Note(note="S", octave=octave)
    elif abs(numSteps) == 1 or abs(numSteps) == 11:
        if numSteps == -1 or numSteps == 11:
            return Note(note="N", noteclass=3, octave=octave)
        else:
            return Note(note="R", noteclass=1, octave=octave)
    elif abs(numSteps) == 2 or abs(numSteps) == 10:
        if numSteps == -2 or numSteps == 10:
            return Note(note="DN", noteclass=2, octave=octave)
        else:
            return Note(note="RG", noteclass=1, octave=octave)
    elif abs(numSteps) == 3 or abs(numSteps) == 9:
        if numSteps == -3 or numSteps == 9:
            return Note(note="DN", noteclass=1, octave=octave)
        else:
            return Note(note="RG", noteclass=2, octave=octave)
    elif abs(numSteps) == 4 or abs(numSteps) == 8:
        if numSteps == -4 or numSteps == 8:
            return Note(note="D", noteclass=1, octave=octave)
        else:
            return Note(note="G", noteclass=3, octave=octave)
    elif abs(numSteps) == 5 or abs(numSteps) == 7:
        if numSteps == -5 or numSteps == 7:
            return Note(note="P", octave=octave)
        else:
            return Note(note="M", noteclass=1, octave=octave)
    elif abs(numSteps) == 6:
            return Note(note="M", noteclass=2, octave=octave)
    return []
    
# Converts a frequency to a pitch. 
def freqToPitch(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    return name[n] + str(octave)

# Takes two pitch frequencies, and determines if the second is an overtone (an integer multiple of the first)
# Returns True if pitchB is an overtone of pitchA
def checkIfOvertone(pitchA, pitchB):
    epsilon = 0.03*pitchB # arbitrary value that scales with the pitches so that values are caught about halfway between other pitch frequencies
    for harmonic in range(2, 21): # checking 20 harmonics
        theoreticalOvertoneValue = harmonic*pitchA
        if theoreticalOvertoneValue > 2*pitchB:
            return False
        if epsilon >= 10:
            if theoreticalOvertoneValue <= pitchB + epsilon and theoreticalOvertoneValue >= pitchB-epsilon:
                return True
        else:
            # frequency resolution is 10 Hz; if epsilon is less than this, then just check at a minimum of 10 hz range
            if theoreticalOvertoneValue <= pitchB + 10 and theoreticalOvertoneValue >= pitchB-10:
                return True
    return False

# Takes a pitch to convert and a pitch representing the sruthi. Returns
# the swara for that pitch.
def convertPitchToSwara(pitch, sruthi):

    numSteps = getNumSteps(sruthi, pitch) # Will be positive, negative, or zero.
    return convertPitchFromSteps(numSteps)


# Takes a ascended-sorted list of pitch frequencies from FFT analysis, and returns a list of the fundamental frequencies found.
def getFundamentalFrequencies(pitchFrequencies):
    if len(pitchFrequencies) < 0:
        return []
    if len(pitchFrequencies) == 1:
        return pitchFrequencies 
    funFreqs = []
    checkedFrequencies = []
    index = len(pitchFrequencies) - 1
    # iterating over list from end to beginning; checking higher frequencies for overtones first.
    for i in range(len(pitchFrequencies) - 1, -1, -1):
        freq = pitchFrequencies[i]
        curFunFreq = None
        if freq in funFreqs:
           index -= 1
           continue
        for low_freq_index in range(index - 1, -1, -1): # checking the left part of the list
            low_freq = pitchFrequencies[low_freq_index]
            if low_freq == freq:
                continue
            if low_freq not in funFreqs and checkIfOvertone(low_freq, freq): # this means that the freq pitch is an overtone of low_freq
                curFunFreq = low_freq
        if curFunFreq is not None and [checkIfOvertone(i, curFunFreq) for i in funFreqs] == [False]*len(funFreqs):
            funFreqs.append(curFunFreq)
            funFreqs = sorted(funFreqs)
            
        index -= 1
    return funFreqs

# Returns a list of all frequencies found, given the given sample rate and a list of samples.
def getFrequencies(rate, samples):
        # plt.figure(1)
        # plt.xlabel('samples')
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

        indexesOfPeaks = peakutils.indexes(fourier_to_plot)
        peakFrequencies = [w[u] for u in indexesOfPeaks]
        
        xxx = peakutils.interpolate(w, fourier_to_plot, ind=indexesOfPeaks)
        pitchPeaks = [freqToPitch(freq) for freq in peakFrequencies]
        funFreqs = getFundamentalFrequencies(peakFrequencies)
        if os.getenv("PRINT_FREQS") is not None:
            print("Peaks: %s" % str(peakFrequencies))

            print("\n---------------------------------------------------------------------")
            print("========> FFs: %s" % str(funFreqs))
            print("---------------------------------------------------------------------\n")
        # print("XXX: %s" % str([freqToPitch(freq) for freq in xxx]))
        # print("Peak Frequencies: %s" % str(pitchPeaks))
        # print()
        plt.figure(1)
        plt.xlabel('frequency')
        plt.ylabel('amplitude')
        plt.plot(w[:int(len(w)/10)], fourier_to_plot[:int(len(fourier_to_plot)/10)])
        # plt.show()
        return funFreqs