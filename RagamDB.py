class Note:
    def __init__(self, note, position=0):
        self.note = note
        self.position = position 
        
    def __eq__(self, other):
        return self.note == other.note and self.position == other.position 
    
    def __repr__(self):
        return "%s%d" % (self.note, self.position)

class Ragam:
    def __init__(self, name, ascendingNotes, descendingNotes, parent=None):
        self.name = name
        self.ascending = ascendingNotes
        self.descending = descendingNotes
        self.parent = parent
        
    def __repr__(self):
        return "%s: %s - %s" % (self.name, ' '.join([str(x) for x in self.ascending]), ' '.join([str(x) for x in self.descending]))
                                
    def __eq__(self, other):
        return self.ascending == other.ascending and self.descending == other.descending and self.name == other.name and self.parent == other.parent
    

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
        with open(filename, 'r') as ragamFile:
            for line in ragamFile:
                if line.strip() == "":
                    continue
                try:
                    indexOfSa = line.index(" S ")
                except ValueError:
                    print("ValueError: %s" % line)
                if line[0].isnumeric():
                    currentParent = line[2:indexOfSa].strip()
                    currentRagam = currentParent
                else:
                    currentRagam = line[:indexOfSa].strip()
                indexOfDash = line.rfind('-')
                arohanam = line[indexOfSa:indexOfDash].strip().split(' ')
                avarohanam = line[indexOfDash + 1:].strip().split(' ')
                arohanamNotes = []
                avarohanamNotes = []
                for note in arohanam:
                    # try:
                    if note == "S" or note == "P":
                        arohanamNotes.append(Note(note))
                    else:
                        try:
                            arohanamNotes.append(Note(note[0], int(note[1])))
                        except IndexError:
                            arohanamNotes.append(Note(note, 1))
                    # except:
                    #     print("Error: Could not parse arohanam for ragam %s" % currentRagam)
                for note in avarohanam:
                    try:
                        if note == "S" or note == "P":
                            avarohanamNotes.append(Note(note))
                        else:
                            avarohanamNotes.append(Note(note[0], int(note[1])))
                    except IndexError:
                        avarohanamNotes.append(Note(note, 1))
                    #     print("Error: Could not parse avarohanam for ragam %s" % currentRagam)
                ragamList.append(Ragam(currentRagam, arohanamNotes, avarohanamNotes, currentParent))
        return ragamList
            
    ## Searches for a ragam based on ascending and descending scales
    # Returns a Ragam object if it finds the appropriate ragam.
    def searchByScales(self, ascendingScale, descendingScale):
        for ragam in self.ragamList:
            if ragam.ascending == ascendingScale and ragam.descending == descendingScale:
                return ragam
        else:
            raise RagamNotFoundError
    
# for ragam in ragamList:
    # if ragam.ascending == [Note("S"), Note("R", 2), Note("G", 3), Note("P"), Note("N", 3), Note("S")] and ragam.descending == [Note("S"), Note("N", 3), Note("P"), Note("G", 3), Note("R", 2), Note("S")]:
        # print(ragam.name)