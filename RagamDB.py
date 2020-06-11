
class Note:
    
    # constructor for Note that takes Note(note, noteclass, octave)
    # Notes are as follows:
    # S0, R1, RG1, RG2, G3, M1, M2, P0, D1, DN1, DN2, N3
    # Octave 0 is lower than S0, Octave 1 is regular singing octave, octave 2 is highest.
    # Octave 1 starts at S0, octave 2 starts at S1
    def __init__(self, note, noteclass=0, octave=1):
        self.note = note
        self.noteclass = noteclass
        self.octave = octave
        self.notes = ["S", "R", "RG", "G", "M", "P", "D", "DN", "N"]

    def __eq__(self, other):
        return False if other is None else self.note == other.note and self.noteclass == other.noteclass and self.octave == other.octave
    
    def __repr__(self):
        return "%s%d: %d" % (self.note, self.noteclass, self.octave)
    
    def __gt__(self, other):
        index1 = self.notes.index(self.note)
        index2 = self.notes.index(other.note)
        if self.octave > other.octave:
            return True
        if self.octave == other.octave:
            if index1 > index2:
                return True 
            if index1 == index2:
                if self.noteclass > other.noteclass:
                    return True
        return False
    
    def __lt__(self, other):
        index1 = self.notes.index(self.note)
        index2 = self.notes.index(other.note)
        if self.octave < other.octave:
            return True
        if self.octave == other.octave:
            if index1 < index2:
                return True 
            if index1 == index2:
                if self.noteclass > other.noteclass:
                    return True
        return False

    
class Transition():
    
    # base is the base note and end is the end note (both of type Note)
    def __init__(self, base, end):
        self.base = base
        self.end = end
        # motion represents the direction of the note: -1 is down, 1 is up, 0 is flat
        self.motion = 0
        if base.note != end.note:
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
    
    def __eq__(self, other):
        return self.motion == other.motion and self.base.note == other.base.note and self.end.note == other.end.note


class Ragam:
    def __init__(self, name, ascendingNotes, descendingNotes, parent=None):
        self.name = name
        self.ascending = ascendingNotes
        self.descending = descendingNotes
        self.parent = parent
        # The transitions list is meant to demonstrate the relationships between notes
        self.transitions = self.__getTransitions(self.ascending) + self.__getTransitions(self.descending)
        
        
    def __getTransitions(self, scale):
        transitionList = []
        for i in range(0, len(scale)):
            for j in range(i, len(scale)):
                transitionList.append(Transition(scale[i], scale[j]))
        return transitionList
        
    def __repr__(self):
        nameLen = len(self.name)
        s = (self.name[:20] + "...:") if nameLen > 20 else self.name + " "*(23 - nameLen) + ":"
        s += "\t" + ' '.join([(x.note + str(x.noteclass)) for x in self.ascending]) + "\n"
        s += " "*(24) + "\t" + ' '.join([(x.note + str(x.noteclass)) for x in self.descending]) + "\n"
        return s
                                
    def __eq__(self, other):
        return self.ascending == other.ascending and self.descending == other.descending and self.name == other.name 
    


class RagamNotFoundError(Exception):
    pass

class RagamDB:
    def __init__(self, filename):
        self.ragamList = self.getRagamListFromFile(filename)
        print("RAGAM LIST LENGTH: %d" % len(self.ragamList))
        
    # Takes a list of ragas and a transition, and returns a list of ragas from the original list that 
    # include the transition.
    def getRagasWithTransition(self, existing_ragas, transition):
        ragas = []
        if existing_ragas == []:
            existing_ragas = self.ragamList
        for ragam in existing_ragas:
            if transition in ragam.transitions:
                ragas.append(ragam)
        return ragas
        
    def getRagamListFromFile(self, filename):
        ragamList = []
        currentParent = ""
        currentRagam = ""
        ragamNameLine = True
        arohanamLine = False
        avarohanamLine = False 
        arohanamNotes = []
        avarohanamNotes = []
        
        noteMap = {"R1": Note(note="R", noteclass=1),
                   "R2": Note(note="RG", noteclass=1),
                   "G1": Note(note="RG", noteclass=1),
                   "R3": Note(note="RG", noteclass=2),
                   "G2": Note(note="RG", noteclass=2),
                   "G3": Note(note="G", noteclass=3),
                   "M1": Note(note="M", noteclass=1),
                   "M2": Note(note="M", noteclass=2),
                   "D1": Note(note="D", noteclass=1),
                   "D2": Note(note="DN", noteclass=1),
                   "N1": Note(note="DN", noteclass=1),
                   "D3": Note(note="DN", noteclass=2),
                   "N2": Note(note="DN", noteclass=2),
                   "N3": Note(note="N", noteclass=3)}
        with open(filename, 'r') as ragamFile:
            for line in ragamFile:
                if line.strip() == "":
                    continue
                if line[0].isnumeric(): # This means that this line is a parent ragam
                    for i in range(len(line)):
                        if not line[i].strip().isnumeric():
                            currentParent = line[i:].strip()
                            currentRagam = line[i:].strip()
                            arohanamLine = True
                            ragamNameLine = False
                            break
                elif ragamNameLine: # This means that this line is a child ragam
                    currentRagam = line.strip()
                    arohanamLine = True
                    ragamNameLine = False
                
                elif arohanamLine:
                    arohanam = line.strip().split(' ')
                    arohanamNotes = []
                    for note in arohanam:
                        if note == "S" or note == "P":
                            if note == "S" and Note(note) in arohanamNotes:
                                arohanamNotes.append(Note(note=note, octave=2))
                            else:
                                arohanamNotes.append(Note(note))
                        else:
                            try:
                                arohanamNotes.append(noteMap[note])
                            except IndexError:
                                print("Index error on arohanam for ragam %s " % currentRagam)
                            except KeyError:
                                print("Note key error for ragam %s" % currentRagam)
                    arohanamLine = False
                    avarohanamLine = True 
                    ragamNameLine = False
                elif avarohanamLine:
                    avarohanam = line.strip().split(' ')
                    avarohanamNotes = []
                    for note in avarohanam:
                        if note == "S" or note == "P":
                            if note == "S" and Note(note=note, octave=2) not in avarohanamNotes:
                                avarohanamNotes.append(Note(note=note, octave=2))
                            else:
                                avarohanamNotes.append(Note(note))
                        else:
                            try:
                                avarohanamNotes.append(noteMap[note])
                            except IndexError:
                                print("Index error on avarohanam for ragam %s " % currentRagam)
                            except KeyError:
                                print("Note key error for ragam %s" % currentRagam)
                    arohanamLine = False
                    avarohanamLine = False 
                    ragamNameLine = True
                    ragamList.append(Ragam(currentRagam, arohanamNotes, avarohanamNotes, currentParent))
                    arohanamNotes = avarohanamNotes = []
                    
        return ragamList
            
    ## Searches for a ragam based on ascending and descending scales
    # Returns a Ragam object if it finds the appropriate ragam.
    def searchByScales(self, ascendingScale, descendingScale):
        for ragam in self.ragamList:
            if ragam.ascending == ascendingScale and ragam.descending == descendingScale:
                return ragam
        else:
            raise RagamNotFoundError
   

