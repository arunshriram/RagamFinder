#! /usr/bin/env python
# Author: Arun Shriram
# This file contains the main functions used for testing the Ragam Finder program, that operate on a 
# high level.

import sys, os, csv, traceback
from aubio import source, pitch
import numpy as np
import matplotlib.pyplot as plt
from statistics import mode
from RagamDB import *
from musicFuncs import *

# Handles all file processing - takes a filename and a sruthi, gets all the frequencies present in the file
# using FFTs, determines the fundamental frequencies, despeckles these fundamental frequencies, and ultimately
# extracts the notes and transitions present in the given file. Returns this list of transitions.
def processFile(filename, sruthi):
    
    downsample = 1
    samplerate = 44100 // downsample

    win_s = 4096 // downsample # fft size
    hop_s = 512  // downsample # hop size

    s = source(filename, samplerate, win_s)
    samplerate = s.samplerate


    accumulated_pitches = {}
   
    print("|============================================|")

    output_list = []
    pitchDict = {"S" : 0, "R": 1, "RG": 2, "G": 3, "M": 4, "P": 5, "D": 6, "DN": 7, "N": 8}
    
    while True: # For loop that iterates over every frame in the given file.
        samples, read = s()
        if read < hop_s:
            break
        pitches = getFrequencies(44100, samples)
                    
        newNotes = [freqToPitch(freq) for freq in pitches]
        
        output_list.append(pitches)
        
        # Printing rough approximation of all notes to see easily
        for note in newNotes:
            swara = convertPitchToSwara(note, sruthi)
            print("\t" * pitchDict[swara.note[0]], end='')
            print("%s" % swara)
            # if note in oldNotes:
            if note not in accumulated_pitches:
                accumulated_pitches[note] = 1
            else:
                accumulated_pitches[note] += 1

        print("|============================================|")
        # oldNotes = newNotes
    
    superwindow_size = 5
        
    # plotNotes(output_list, sruthi, filename, False)
    
    output_list = despecklePitches(output_list, superwindow_size, sruthi)
    
    note_list = extractNotesFromDespeckledFreqs(output_list[superwindow_size:len(output_list) - superwindow_size], sruthi)
    
    transition_list = determineTransitionsFromNotes(note_list)
    
    #-----------------------------------------------------------------------------------

    # GRAPH OF NOTES AFTER DESPECKLE    
    # plotNotes(output_list, sruthi, filename, True)
    
    #-----------------------------------------------------------------------------------

    return transition_list

# Given a set of frequencies, a sruthi, a filename, and a boolean value representing whether
# this list of freqs has been despeckled, plots the given notes.
def plotNotes(original_freq_list, sruthi, filename, despeckled):
    notes_to_graph = []
    
    # Convert all original_freq_list to notes
    for freq in original_freq_list:
        if type(freq) == list:
            if len(freq) >= 1:
                freq = freq[0]
            elif len(freq) == 0:
                continue
        pitch = freqToPitch(freq)
        note = convertPitchToSwara(pitch, sruthi)
        notes_to_graph.append(note)
    y = []
    count = 0;
    noteToNums = {"S0": 0, "R1": 1, "RG1": 2, "RG2": 3, "G3": 4, "M1": 5, "M2": 6, "P0": 7, 
                  "D1": 8, "DN1": 9, "DN2": 10, "N3": 11}
    for note in notes_to_graph: 
        frame_notes = []
        val_to_append = noteToNums[note.note + str(note.noteclass)]
        if note.octave > 1:
            val_to_append += 12
        frame_notes.append(val_to_append)
        y.append(tuple(frame_notes))
        count += 1
    x = list(range(count))
    for xe, ye in zip(x, y):
        plt.scatter([xe]*len(ye), ye, c=[[0, 0, 0]])
    plt.title("Plot of all frames' notes for %s %s" % (filename, "(after despeckle)" if despeckled else "(before despeckle)"))
    plt.xlabel("Frame number")
    plt.ylabel("Note(s) identified for frame")
    plt.xticks(np.arange(0, count, 4))
    plt.yticks(np.arange(0, max(max(y)), 1))

    # plt.show()
    
# Takes a list of lists of pitches, a super window size, and a sruthi. Each list of pitches represents all the pitches
# discovered in one frame. So if there are 5 frames analyzed in total, and 1 pitch found per frame, then the pitchList 
# would be [[a], [b], [c], [d], [e]], where a, b, c, d, and e represent frequencies. 
def despecklePitches(pitchList, superwindow_size, sruthi):
    middle_frame_index = int(superwindow_size/2)
    superwindow = pitchList[:superwindow_size] # if x is superwindow size, take the first x elements from the input list
    dataIndex = superwindow_size # dataIndex is used to get the next pitch when sliding the superwindow
    while dataIndex <= len(pitchList):
        all_superwindow_freqs = [] # will contain all the frequencies for the entire superwindow
        for frame in superwindow:
            for pitch in frame:
                all_superwindow_freqs.append(pitch)
        try:
            most_common_freq = mode(all_superwindow_freqs)
            most_common_note = convertPitchToSwara(freqToPitch(most_common_freq), sruthi)
        except:
            # traceback.print_exc()
            # superwindow = []
            # print()
            # print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
            # print("No most common swara found.")
            # print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
            # print()
            # Remove the first element of the superwindow and add the next element
            old_mid_frame = pitchList[middle_frame_index]
            
            # since no most common freq, just going to pick the second half of the superwindow.
            defaultPitch = pitchList[middle_frame_index + 1]
            if defaultPitch != []:
                defaultPitch = [defaultPitch[0]]
            pitchList[middle_frame_index] = defaultPitch
            # print("Swapped %s with %s" % (old_mid_frame, pitchList[middle_frame_index]))
            
            # Now, remove first element from superwindow to move the window by 1 frame
            
            # This makes sure that the first element of new superwindow is the second element of old superwindow
            new_low_index = (middle_frame_index - int(superwindow_size/2)) + 1 
            new_high_index = middle_frame_index + int(superwindow_size/2) + 1
            superwindow = pitchList[new_low_index:new_high_index]
            middle_frame_index += 1 # superwindow will be offset by 1; move the middle index pointer up 1 frame.
            # add the next frame's data to the superwindow
            if dataIndex < len(pitchList):
                superwindow.append(pitchList[dataIndex])
            else:
                break
            dataIndex += 1
            continue
            
        # print()
        # print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
        # print("Most common swara for this superwindow: %s" % most_common_note)
        # print("+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
        # print()
        old_mid_frame = pitchList[middle_frame_index]
        pitchList[middle_frame_index] = [most_common_freq]
        # print("Swapped %s with %s" % (old_mid_frame, pitchList[middle_frame_index]))
        
        # Now, remove first element from superwindow to move the window by 1 frame
        
        # This makes sure that the first element of new superwindow is the second element of old superwindow
        new_low_index = (middle_frame_index - int(superwindow_size/2)) + 1 
        new_high_index = middle_frame_index + int(superwindow_size/2) + 1
        superwindow = pitchList[new_low_index:new_high_index]
        middle_frame_index += 1 # superwindow will be offset by 1; move the middle index pointer up 1 frame.
        # add the next frame's data to the superwindow
        if dataIndex < len(pitchList):
            superwindow.append(pitchList[dataIndex])
        dataIndex += 1
    print("Finished despeckling.")
    return [x[0] for x in pitchList if x != []]
    
# Takes a list of pitch frequencies (after despeckling) and returns a list of Notes
# in the order that they are given in the input frequencies.
def extractNotesFromDespeckledFreqs(freqs, sruthi):
    currentFreq = None
    extractedNotes = []
    lastAddedNote = None
    if freqs == []:
        return extractedNotes
    
    # Notes are only extracted if there are at least two instances of a frequency in a row
    currentFreq = freqs[0]
    for i in range(1, len(freqs)):
        freq = freqs[i]
        if freq == currentFreq and freq != None:
            pitch = freqToPitch(freq)
            note = convertPitchToSwara(pitch, sruthi)
            if lastAddedNote != note:
                extractedNotes.append(note)
                lastAddedNote = note 
        else:
            currentFreq = freq 
    
    return extractedNotes

# Returns True if the given note (not considering the note class) exists in the given
# list of transitions. Returns False otherwise.
def noteExistsInTransitionList(note, transitionList):
    for transition in transitionList:
        if note == transition.base or note == transition.end:
            return True
    return False
    
# Given the note list from the recording, returns a list of Transitions from notes.
def determineTransitionsFromNotes(noteList):
    if len(noteList) < 2:
        return []
    transitions = []
    special_cases = [] # a list of tuples, with each tuple containing note(s) and the note(s) that the first transition(s) to
    previousNote = noteList[0]
    for i in range(1, len(noteList)):
        transitions.append(Transition(previousNote, noteList[i]))
        previousNote = noteList[i]
        
    return transitions 

    
def main():
    
    if len(sys.argv) < 3:
        print("Usage:   python3 RagamFinder.py audio_filename sruthi")
        print("         audio_filename : The music file that contains ragam to be identified")
        print("         sruthi         : The tonic pitch of the given audio file")
        print("Example: python3 RagamFinder.py kalyani.mp3 G")
        return
    # Parse arguments
    
    # Given filename
    file = sys.argv[1]
    # Manually input sruthi
    sruthi = str(sys.argv[2]) + "3"
    
   
    
    print()
    print("Beginning ragam analysis...")
    print()
    
    
    filename = file[:file.index('.')]
    transitions = processFile(file, sruthi)
    
     # Initialize the Ragam Database
    ragamDB = RagamDB("reference/ragam_list.txt")
    ragas_that_meet_criteria = []
    print()
    print("|=======================================|")
    print("|         Transitions Discovered        |")
    print("|=======================================|")
    for transition in transitions:
        print(" "*12 + str(transition))

    print()
    print()
    for transition in transitions:
        ragas_that_meet_criteria = ragamDB.getRagasWithTransition(ragas_that_meet_criteria, transition)
        print(len(ragas_that_meet_criteria)) # for debugging 
            
    print()
    print()
    print("|================================================================|")
    print("|                         Possible Ragas                         |")
    print("|================================================================|")
    for ragam in ragas_that_meet_criteria:
        print("  " + str(ragam))
    
if __name__ == '__main__':
    main()