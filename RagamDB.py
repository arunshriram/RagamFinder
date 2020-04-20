class Note:
    
    # constructor for Note that takes Note(note, pitchclass, octave)
    # Octave 0 is lower than S0, Octave 1 is regular singing octave, octave 2 is highest.
    # Octave 1 starts at S0, octave 2 starts at S1
    def __init__(self, note, pitchclass=0, octave=1):
        self.note = note
        self.pitchclass = pitchclass
        self.octave = octave
        
    # constructor for Note that takes Note(notepitchclass, octave), i.e. Note("D#3")
    # Octave 0 is lower than S0, Octave 1 is regular singing octave, octave 2 is highest.
    # Octave 1 starts at S0, octave 2 starts at S1
    def __init__(self, notewithpitchclass, octave=1):
        self.octave = octave
        if len(notewithpitchclass) == 1:
            self.note = notewithpitchclass
            self.pitchclass = 0
        else:
            self.note = notewithpitchclass[:len(notewithpitchclass) - 1]
            self.pitchclass = int(notewithpitchclass[len(notewithpitchclass) - 1:])
    
    def __eq__(self, other):
        return self.note == other.note and self.pitchclass == other.pitchclass and self.octave == other.octave
    
    def __repr__(self):
        return "%s%d: %d" % (self.note, self.pitchclass, self.octave)

class Ragam:
    def __init__(self, name, ascendingNotes, descendingNotes, parent=None):
        self.name = name
        self.ascending = ascendingNotes
        self.descending = descendingNotes
        self.parent = parent
        
    def __repr__(self):
        return "%s: %s - %s" % (self.name, ' '.join([str(x) for x in self.ascending]), ' '.join([str(x) for x in self.descending]))
                                
    def __eq__(self, other):
        return self.ascending == other.ascending and self.descending == other.descending and self.name == other.name 
    

# rag = Ragam("mohanam", [Note("S"), Note("R", 2), Note("G", 3), Note("P"), Note("D", 2), Note("S")], [Note("S"), Note("D", 2), Note("P"), Note("G", 3), Note("R", 2), Note("S")], "harikambhoji")
# print(rag)

class RagamNotFoundError(Exception):
    pass

class RagamDB:
    def __init__(self, filename):
        self.ragamList = self.getRagamListFromFile(filename)
        
    def getRagamListFromFile(self, filename):
        ragamList = []
        currentParent = ""
        currentRagam = ""
        ragamNameLine = True
        arohanamLine = False
        avarohanamLine = False 
        arohanamNotes = []
        avarohanamNotes = []
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
                            arohanamNotes.append(Note(note))
                        else:
                            try:
                                arohanamNotes.append(Note(note[0], int(note[1])))
                            except IndexError:
                                print("Index error on arohanam for ragam %s " % currentRagam)
                    arohanamLine = False
                    avarohanamLine = True 
                    ragamNameLine = False
                elif avarohanamLine:
                    avarohanam = line.strip().split(' ')
                    avarohanamNotes = []
                    for note in avarohanam:
                        if note == "S" or note == "P":
                            avarohanamNotes.append(Note(note))
                        else:
                            try:
                                avarohanamNotes.append(Note(note[0], int(note[1])))
                            except IndexError:
                                print("Index error on avarohanam for ragam %s " % currentRagam)
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
   