#! /usr/bin/env python

import sys, time
from aubio import source, pitch
import os.path
from numpy import array, ma
import matplotlib.pyplot as plt
from demo_waveform_plot import get_waveform_plot, set_xlabels_sample2time

# Relates MIDI note numbers to pitches
pitchDictionary = {0:"C", 1:"C#", 2:"D", 3:"D#", 4:"E", 5:"F", 6:"F#", 7:"G", 8:"G#", 9:"A", 10:"A#", 11:"B"}
pitchNumberDictionary = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

def convertMIDIToNote(noteNumber):
    return pitchDictionary[noteNumber%12] + "_" + str(int((noteNumber - 24)//12))

class AudioAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        downsample = 1
        self.samplerate = 44100 // downsample
        # if len( sys.argv ) > 2: self.samplerate = int(sys.argv[2])

        win_s = 4096 // downsample # fft size
        self.hop_s = 512  // downsample # hop size

        self.s = source(filename, self.samplerate, self.hop_s)
        self.samplerate = self.s.samplerate

        self.tolerance = 0.8

        self.pitch_o = pitch("yin", win_s, self.hop_s, self.samplerate)
        self.pitch_o.set_unit("midi")
        self.pitch_o.set_tolerance(self.tolerance)

        self.pitches = []
        self.confidences = []

        self.pitch_frequencies = {}
    
    def getMostFrequentPitches(self):
        # print()
        # print("++++++++++++++++++++++++++++++++")
        # print("Beginning to analyze pitches...")
        # print("++++++++++++++++++++++++++++++++")
        # print()
        start = time.time()
        # total number of frames read
        total_frames = 0
        while True:
            samples, read = self.s()
            pitch = self.pitch_o(samples)[0]
            #pitch = int(round(pitch))
            confidence = self.pitch_o.get_confidence()
            #if confidence < 0.8: pitch = 0.
            #print("%f %f %f" % (total_frames / float(self.samplerate), pitch, confidence))
            self.pitches += [pitch]
            note = convertMIDIToNote(round(pitch))
            if(note not in self.pitch_frequencies):
                self.pitch_frequencies[note] = 1
            else:
                self.pitch_frequencies[note] += 1
            self.confidences += [confidence]
            total_frames += read
            if read < self.hop_s: break

        if 0: sys.exit(0)

        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print("Finished processing file in %d seconds" % (time.time() - start))
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print()
        # print("Total number of pitches found: %d" % len(self.pitches))
        # print()
        # print("Here are the pitches and their respective frequencies:")
        return sorted(self.pitch_frequencies.items(), reverse=True, key = lambda kv: (kv[1], kv[0]))
        # return self.pitches
    
    def array_from_text_file(self, filename, dtype = 'float'):
        filename = os.path.join(os.path.dirname(__file__), filename)
        return array([line.split() for line in open(filename).readlines()],
            dtype = dtype)
            
    def plotPitches(self):
        skip = 1

        pitches = array(self.pitches[skip:])
        confidences = array(self.confidences[skip:])
        times = [t * self.hop_s for t in range(len(pitches))]

        fig = plt.figure()

        ax1 = fig.add_subplot(311)
        ax1 = get_waveform_plot(self.filename, samplerate = self.samplerate, block_size = self.hop_s, ax = ax1)
        plt.setp(ax1.get_xticklabels(), visible = False)
        ax1.set_xlabel('')

        ax2 = fig.add_subplot(312, sharex = ax1)
        ground_truth = os.path.splitext(self.filename)[0] + '.f0.Corrected'
        if os.path.isfile(ground_truth):
            ground_truth = self.array_from_text_file(ground_truth)
            true_freqs = ground_truth[:,2]
            true_freqs = ma.masked_where(true_freqs < 2, true_freqs)
            true_times = float(self.samplerate) * ground_truth[:,0]
            ax2.plot(true_times, true_freqs, 'r')
            ax2.axis( ymin = 0.9 * true_freqs.min(), ymax = 1.1 * true_freqs.max() )
        # plot raw pitches
        ax2.plot(times, pitches, '.g')
        # plot cleaned up pitches
        cleaned_pitches = pitches
        #cleaned_pitches = ma.masked_where(cleaned_pitches < 0, cleaned_pitches)
        #cleaned_pitches = ma.masked_where(cleaned_pitches > 120, cleaned_pitches)
        cleaned_pitches = ma.masked_where(confidences < self.tolerance, cleaned_pitches)
        ax2.plot(times, cleaned_pitches, '.-')
        #ax2.axis( ymin = 0.9 * cleaned_pitches.min(), ymax = 1.1 * cleaned_pitches.max() )
        #ax2.axis( ymin = 55, ymax = 70 )
        plt.setp(ax2.get_xticklabels(), visible = False)
        ax2.set_ylabel('Estimated frequency (midi)')

        # plot confidence
        ax3 = fig.add_subplot(313, sharex = ax1)
        # plot the confidence
        ax3.plot(times, confidences)
        # draw a line at tolerance
        ax3.plot(times, [self.tolerance]*len(confidences))
        ax3.axis( xmin = times[0], xmax = times[-1])
        ax3.set_ylabel('confidence')
        set_xlabels_sample2time(ax3, times[-1], self.samplerate)
        plt.show()
        #plt.savefig(os.path.basename(filename) + '.svg')
        
def determinePitchBySubdominantDominant(fiveMostFrequentPitches):
    sumTotals = {}
    for pitchTuple in fiveMostFrequentPitches:
        pitch = pitchTuple[0]
        sumTotals[pitch] = 0
        for pTup in fiveMostFrequentPitches:
            checkPitch = pTup[0].split()
            checkFreq = pTup[1]
            if checkPitch != pitch:
                # Checking if this pitch is the dominant of the outer loop's pitch
                normalPitchNumber = pitchNumberDictionary[checkPitch] - 7
                if normalPitchNumber < 0:
                    normalPitchNumber = 12 - abs(normalPitchNumber)
                if pitchDictionary[normalPitchNumber] == pitch:
                    sumTotals[pitch] += checkFreq
                    continue
                # Checking if this pitch is the subdominant of the outer loop's pitch
                normalPitchNumber = pitchNumberDictionary[checkPitch] - 5
                if normalPitchNumber < 0:
                    normalPitchNumber = 12 - abs(normalPitchNumber)
                if pitchDictionary[normalPitchNumber] == pitch:
                    sumTotals[pitch] += checkFreq
    
    max = -1
    mostLikelyPitch = "Unknown pitch"
    for pitch in sumTotals:
        if sumTotals[pitch] > max:
            max = sumTotals[pitch]
            mostLikelyPitch = pitch
    return mostLikelyPitch
        
def main():
    # if len(sys.argv) < 2:
    #     print("Usage: %s <filename> [self.samplerate]" % sys.argv[0])
    #     sys.exit(1)

    # filename = sys.argv[1]

    # audioAnalyzer = AudioAnalyzer(filename)
    # audioAnalyzer.getPitches()
    
    print()
    print("Beginning sruthi analysis...")
    print()
    successTracker = {}
    count = 1
    for filenam in os.listdir("TestData"):
        if(not (filenam.endswith("mp3") or filenam.endswith("m4a") or filenam.endswith("wav"))):
            continue
        audioAnalyzer = AudioAnalyzer("TestData/" + filenam)
        
        file = filenam.split('.')[0]
        print("%d. Verifying %s......" % (count, file), end="")
        pitches = audioAnalyzer.getMostFrequentPitches()
        if(pitches[0][0].split('_')[0] == file.split("_")[0]):
            print("Success")
            successTracker[filenam] = "Success"
        else:
            print("Failure! Found %s instead." % pitches[0][0])
            successTracker[filenam] = "...Failure"
            
        numPitches = len(audioAnalyzer.pitches)
        print("\t%s \n\tTotal # of pitches is %d \n\tMost frequent pitch makes up %d%% of pitches" % (str(pitches[:10]), numPitches, 100*(pitches[0][1]/float(numPitches))))
        # print()
        # print("I think the pitch is %s" % determinePitchBySubdominantDominant(pitches[:5]))
        print('\n')
    # audioAnalyzer.plotPitches()
        count += 1

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
    print("Success rate: %f" % (successes/float(total)))
    
if __name__ == '__main__':
    main()