#! /usr/bin/env python

import sys, os, csv, traceback
from aubio import source, pitch
import os.path
from numpy import array, ma
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile 
from statistics import mode
import peakutils 
from RagamDB import *
from musicFuncs import *

    
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


            
def getFrequencies(rate, samples):
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
        funFreqs = getFundamentalFrequencies(peakFrequencies)
        if os.getenv("PRINT_FREQS") is not None:
            print("Peaks: %s" % str(peakFrequencies))

            print("\n---------------------------------------------------------------------")
            print("========> FFs: %s" % str(funFreqs))
            print("---------------------------------------------------------------------\n")
        # print("XXX: %s" % str([freqToPitch(freq) for freq in xxx]))
        # print("Peak Frequencies: %s" % str(pitchPeaks))
        # print()
        # plt.figure(1)
        # plt.xlabel('frequency')
        # plt.ylabel('amplitude')
        # plt.plot(w[:int(len(w)/10)], fourier_to_plot[:int(len(fourier_to_plot)/10)])
        # plt.show()
        return funFreqs
    
def processFile(filename, sruthi):
    
    downsample = 1
    samplerate = 44100 // downsample
    if len( sys.argv ) > 2: samplerate = int(sys.argv[2])

    win_s = 4096 // downsample # fft size
    hop_s = 512  // downsample # hop size

    s = source(filename, samplerate, win_s)
    samplerate = s.samplerate


    accumulated_pitches = {}
    # samples, read = s()
    # pitches = getFrequencies(44100, samples)
    # oldNotes = [freqToPitch(freq) for freq in pitches]
    # for note in oldNotes:
    #         print("%s" % (convertPitchesToSwaras([note], sruthi)[0][0]))
    print("|============================================|")

    count = 0
    superwindow = []
    cur_note = None
    transitions = []
    
    output_list = []
    
    pitchDict = {"S" : 0, "R": 1, "G": 2, "M": 3, "P": 4, "D": 6, "N": 7}
    
    while True: # For loop that iterates over every frame in the given file.
       
        samples, read = s()
        count += 1
        if read < hop_s:
            break
        pitches = getFrequencies(44100, samples)

        
                    
        newNotes = [freqToPitch(freq) for freq in pitches]
        
        x = convertPitchesToSwaras(newNotes, sruthi)
        output_list.append(x)
        
        for note in newNotes:
            swara = convertPitchesToSwaras([note], sruthi)[0][0]
            print("\t" * pitchDict[swara.note[0]], end='')
            print("%s" % swara)
            # if note in oldNotes:
            if note not in accumulated_pitches:
                accumulated_pitches[note] = 1
            else:
                accumulated_pitches[note] += 1

        print("|============================================|")
        # oldNotes = newNotes
        
        superwindow.append(pitches)
        if count%5 == 0:
            all_freqs = []
            
            for window in superwindow:
                for pitch in window:
                    all_freqs.append(pitch)
            
            try:
                most_common = mode(all_freqs)
                most_common = convertPitchesToSwaras([freqToPitch(most_common)], sruthi)[0][0]
                if cur_note is None:
                    cur_note = most_common
                else:
                    transitions.append(Transition(cur_note, most_common))
                    cur_note = most_common
                    
            except:
                # traceback.print_exc()
                superwindow = []
                print()
                print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
                print("No most common swara found.")
                print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
                print()
                continue
                
            print()
            print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
            print("Most common swara for this superwindow: %s" % most_common)
            print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
            print()
            superwindow = []
            
    if len(transitions) == 0:
        transitions.append(cur_note)
    print(transitions)
    print ("COUNT: %d " % count)
    y = []
    count = 0;
    # with open("output.csv", 'w') as csvfile:
    #     writer = csv.writer(csvfile)
    noteToNums = {"S0": 0, "R1": 1, "R2": 2, "G1": 2, "R3": 3, "G2": 3, "G3": 4, 
            "M1": 5, "M2": 6, "P0": 7, "D1": 8, "D2": 9, "N1": 9, "D3": 10,
            "N2": 10, "N3": 11}
    for frame in output_list: 
        frame_notes = []
        for note_list in frame:
            note = note_list[0]
            val_to_append = noteToNums[note.note + str(note.pitchclass)]
            if note.octave > 1:
                val_to_append += 12
            frame_notes.append(val_to_append)
        y.append(tuple(frame_notes))
        count += 1
    x = list(range(count))
    for xe, ye in zip(x, y):
        plt.scatter([xe]*len(ye), ye, c=[[0, 0, 0]])
    plt.title("Plot of all frames' notes for Mayamalavagowla Arohanam")
    plt.xlabel("Frame number")
    plt.ylabel("Note(s) identified for frame")
    plt.xticks(np.arange(0, count, 2))
    plt.show()
    # print("Total frames: ", total_frames)
    # print(mostFrequentPitches)
    return accumulated_pitches.items()
    # return sorted(accumulated_pitches.items(), reverse=False, key = lambda kv: (kv[1], kv[0]))
    
    

def testRagam():
    arohanam = [Note("S", 1), Note("R", 2, 1), Note("G", 3, 1), Note("P", 1), Note("N", 3, 1), Note("S", 2)]
    avarohanam = [Note("S", 2), Note("N", 3, 1), Note("D", 2, 1), Note("P", 1), Note("M", 2, 1), Note("G", 3, 1), Note("R", 2, 1), Note("S", 1)]
    ragdb = RagamDB("ragam_list.txt")
    print(ragdb.searchByScales(arohanam, avarohanam))
    
def testFile(filename, sruthi):
    pitches = processFile(filename, sruthi)
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
            
    
def main():
    # testRagam()
    print()
    print("Beginning sruthi analysis...")
    print()
    
    #isolating non-noise fundamental pitches
    file = "mayamalavagowla_arohanam_g.mp3"
    sruthi = "G3"
    filename = file[:file.index('.')]
    x = testFile("%s" % file, sruthi)
    pitches = [pitch for pitch in x ]
    # with open("output/%s.csv" % filename, 'w') as csvfile:
    #     writer = csv.writer(csvfile)
    for pitch in pitches:
    #         writer.writerow([convertPitchesToSwaras([pitch[0]], sruthi)[0][0], pitch[1]])
        print("Swara: %s, Count: %d" % (convertPitchesToSwaras([pitch[0]], sruthi)[0][0], pitch[1]))
    
    
if __name__ == '__main__':
    main()