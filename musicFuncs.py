from math import log2, pow
from RagamDB import *

class Transition():
    
    # base is the base note and end is the end note (both of type Note)
    def __init__(self, base, end):
        self.base = base
        self.end = end
        # motion represents the direction of the note: -1 is down, 1 is up, 0 is flat
        self.motion = 0
        if end > base:
            self.motion = 1
        elif end < base:
            self.motion = -1
    
    def __repr__(self):
        direction = "flat"
        if self.motion == 1:
            direction = "up"
        elif self.motion == -1:
            direction = "down"
        return "%s -> %s, %s" % (self.base, self.end, direction)



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
        return [Note("S", octave=octave)]
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