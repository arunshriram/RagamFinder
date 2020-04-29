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
        return [Note("S", octave)]
    elif abs(numSteps) == 12:
        if numSteps == 12:
            return [Note("S", octave)]
        else:
            return [Note("S", octave)]
    elif abs(numSteps) == 1 or abs(numSteps) == 11:
        if numSteps == -1 or numSteps == 11:
            return [Note("N3", octave)]
        else:
            return [Note("R1", octave)]
    elif abs(numSteps) == 2 or abs(numSteps) == 10:
        if numSteps == -2 or numSteps == 10:
            return [Note("D3", octave), Note("N2", octave)]
        else:
            return [Note("R2", octave), Note("G1", octave)]
    elif abs(numSteps) == 3 or abs(numSteps) == 9:
        if numSteps == -3 or numSteps == 9:
            return [Note("D2", octave), Note("N1", octave)]
        else:
            return [Note("R3", octave), Note("G2", octave)]
    elif abs(numSteps) == 4 or abs(numSteps) == 8:
        if numSteps == -4 or numSteps == 8:
            return [Note("D1", octave)]
        else:
            return [Note("G3", octave)]
    elif abs(numSteps) == 5 or abs(numSteps) == 7:
        if numSteps == -5 or numSteps == 7:
            return [Note("P", octave)]
        else:
            return [Note("M1", octave)]
    elif abs(numSteps) == 6:
            return [Note("M2", octave)]
    return []
    
def freqToPitch(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    return name[n] + str(octave)

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
        numberOfOvertones = 0
        curFunFreq = None
        if freq in funFreqs:
           index -= 1
           continue
        for low_freq_index in range(index - 1, -1, -1): # checking the left part of the list
            low_freq = pitchFrequencies[low_freq_index]
            if low_freq == freq:
                continue
            if low_freq not in funFreqs and checkIfOvertone(low_freq, freq): # this means that the freq pitch is an overtone of low_freq
                numberOfOvertones += 1
                curFunFreq = low_freq
        if numberOfOvertones > 0 and [checkIfOvertone(i, curFunFreq) for i in funFreqs] == [False]*len(funFreqs):
            funFreqs.append(curFunFreq)
            
        index -= 1
    return funFreqs

# Takes two pitch frequencies, and determines if the second is an overtone (an integer multiple of the first)
# Returns True if pitchB is an overtone of pitchA
def checkIfOvertone(pitchA, pitchB):
    epsilon = 0.03*pitchB # arbitrary value that scales with the pitches so that values are caught about halfway between other pitch frequencies
    for harmonic in range(2, 16): # checking 15 harmonics
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
            
def showPlotForSample(rate, samples):
        # plt.figure(1)
        # plt.xlabel('time')
        # plt.ylabel('amplitude')
        # plt.plot(samples)
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
        print("Peaks: %s" % str(peakFrequencies))
        funFreqs = getFundamentalFrequencies(peakFrequencies)
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
    
def processFile(filename):
    
    downsample = 1
    samplerate = 44100 // downsample
    if len( sys.argv ) > 2: samplerate = int(sys.argv[2])

    win_s = 4096 // downsample # fft size
    hop_s = 512  // downsample # hop size

    s = source(filename, samplerate, win_s)
    samplerate = s.samplerate


    accumulated_pitches = {}
    samples, read = s()
    pitches = showPlotForSample(44100, samples)
    oldNotes = [freqToPitch(freq) for freq in pitches]
    count = 0
    while True: # For loop that iterates over every frame in the given file.
        if read < hop_s:
            break
        samples, read = s()
        count += 1
        pitches = showPlotForSample(44100, samples)
        newNotes = [freqToPitch(freq) for freq in pitches]
        continuedNotes = []
        for note in newNotes:
            if note in oldNotes:
                continuedNotes.append(note)
        
        oldNotes = newNotes
        
        for pitch in continuedNotes:
            if pitch not in accumulated_pitches:
                accumulated_pitches[pitch] = 1
            else:
                accumulated_pitches[pitch] += 1
                
    print ("COUNT: %d " % count)
    # print("Total frames: ", total_frames)
    # print(mostFrequentPitches)
    return sorted(accumulated_pitches.items(), reverse=False, key = lambda kv: (kv[1], kv[0]))

def testRagam():
    arohanam = [Note("S", 1), Note("R", 2, 1), Note("G", 3, 1), Note("P", 1), Note("N", 3, 1), Note("S", 2)]
    avarohanam = [Note("S", 2), Note("N", 3, 1), Note("D", 2, 1), Note("P", 1), Note("M", 2, 1), Note("G", 3, 1), Note("R", 2, 1), Note("S", 1)]
    ragdb = RagamDB("ragam_list.txt")
    print(ragdb.searchByScales(arohanam, avarohanam))
    
def testFile(filename):
    pitches = processFile(filename)
    return pitches

def testAllData():
    successTracker = {}
    count = 1
    for filenam in os.listdir("TestData"):
        if(not (filenam.endswith("mp3") or filenam.endswith("m4a") or filenam.endswith("wav"))):
            continue
        file_to_process = "TestData/" + filenam
        
        file = filenam.split('.')[0]
        print("%d. Verifying %s......" % (count, file), end="")
        pitches = processFile(file_to_process)
        print(pitches)
        if(pitches[0][0] == file.split("_")[0]):
            print("Success")
            successTracker[filenam] = "Success"
        else:
            print("Failure! Found %s instead." % pitches[0][0])
            successTracker[filenam] = "...Failure"
            
        print('\n')
        count += 1
    # audioAnalyzer.plotPitches()

    # Print brief summary report
    count = 1
    print()
    successes = 0
    total = 0
    for item in successTracker:
        print("%d. %s\t.....%s" % (count, item, successTracker[item]))
        if successTracker[item] == "Success":
            successes += 1
        total += 1
        count += 1
    print()
    print("Success rate: %s%%" % ('{0:.2f}'.format(100*(successes/float(total)))))

# Takes a list of pitches (presumably from a given frame) and a pitch representing the sruthi. The
# sruthi will only ever be going up from C4 to C5. 
def convertPitchesToSwaras(pitches, sruthi):
    converted_pitches = [] # 2D list; there are 16 possible notes for 12 positions. There are overlaps
    # between the R's and G's, and between the D's and N's. The order is:
    # S, R1, R2/G1, R3/G2, G3, M1, M2, P, D1, D2/N1, D3/N2, N3. 
    # If a pitch is in the position of a note that could possibly be another, a list representing both the
    # notes is appended to converted_pitches list. Otherwise, a list of only one note will be appended.
    for pitch in pitches:
        numSteps = getNumSteps(sruthi, pitch) # Will be positive, negative, or zero.
        converted_pitches.append(convertPitchFromSteps(numSteps))
    return converted_pitches
            
    
def main():
    # testRagam()
    print()
    print("Beginning sruthi analysis...")
    print()
    
    #isolating non-noise fundamental pitches
    x = testFile("maya_notes/s0.mp3")
    pitches = [pitch for pitch in x ]
    for pitch in pitches:
        print("Swara: %s, Count: %d" % (convertPitchesToSwaras([pitch[0]], "G3")[0][0], pitch[1]))
    
    
if __name__ == '__main__':
    main()