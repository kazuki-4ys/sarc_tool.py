import utils, math, shutil
Utils = utils.Utils

class Saht:
    def __init__(self, rawData):
        if type(rawData) is dict:
            self.hashes = rawData
            self.valid = True
            return
        self.hashes = dict()
        if Utils.bytesToString(rawData, 0, 4) != 'SAHT':
            self.valid = False
            return
        self.alignment = Utils.bytesToU32(rawData, 8, True)
        count = Utils.bytesToU32(rawData, 0xC, True)
        curOffset = 0x10
        i = 0
        while curOffset < len(rawData) and i < count:
            curFileName = Utils.bytesToString(rawData, curOffset + 4, None)
            self.hashes[Utils.bytesToU32(rawData, curOffset, True)] = curFileName
            curOffset += math.ceil((4 + len(curFileName) + 1) / self.alignment) * self.alignment
            i += 1
        self.valid = True
    def __add__(self, other):
        if self.valid and other.valid:
            dest.valid = True
            self.hashes.update(other.hashes)
            return Saht(self.hashes)
        else:
            return Saht(bytearray(4))
    def save(self):
        self.hashes = dict(sorted(self.hashes.items(), key=lambda x:x[0]))
        dest = bytearray(16)
        for hash, fileName in self.hashes.items():
            curHashDest = bytearray((((4 + len(fileName) + 1 - 1) >> 4) + 1) << 4)
            Utils.U32ToBytes(curHashDest, 0, hash, True)
            Utils.stringToBytes(curHashDest, 4, None, fileName)
            dest = dest + curHashDest
        Utils.stringToBytes(dest, 0, 4, 'SAHT')
        Utils.U32ToBytes(dest, 4, len(dest), True)
        Utils.U32ToBytes(dest, 8, 0x10, True)
        Utils.U32ToBytes(dest, 0xC, len(self.hashes), True)
        return dest

class SfatNode:
    def __init__(self, hash, fileName, attribute, rawData):
        self.hash = hash
        self.fileName = fileName
        self.attribute = attribute
        self.rawData = rawData
    def save(self, destDir):
        if self.fileName is None:
            destName = hex(self.hash)
            destName = destName[2:]
            destName = '0' * (8 - len(destName)) + destName
            destName = destName.upper()
            return Utils.bytesToFile(self.rawData, destDir + '0x' + destName)
        else:
            return Utils.bytesToFile(self.rawData, destDir + self.fileName)

class Sarc():
    def __init__(self, rawData, hashTableData):
        self.valid = False
        self.hashTable = None
        if type(rawData) is str:
            self.fromDir(rawData)
            return
        self.rawData = rawData
        if Utils.bytesToString(self.rawData, 0, 4) != 'SARC':
            return
        bom = Utils.bytesToU16(self.rawData, 6, False)
        if bom == 0xFFFE:
            self.isLE = True
        elif bom == 0xFEFF:
            self.isLE = False
        else:
            return
        sfatOffset = Utils.bytesToU16(self.rawData, 4, self.isLE)
        fileDataOffset = Utils.bytesToU32(self.rawData, 0xC, self.isLE)
        if Utils.bytesToString(self.rawData, sfatOffset, 4) != 'SFAT':
            return
        sfatHeadSize = Utils.bytesToU16(self.rawData, sfatOffset + 4, self.isLE)
        self.nodes = [None] * (Utils.bytesToU16(self.rawData, sfatOffset + 6, self.isLE))
        nodeOffset = sfatOffset + sfatHeadSize
        self.sfntOffset = nodeOffset + (len(self.nodes) << 4)
        if Utils.bytesToString(self.rawData, self.sfntOffset, 4) != 'SFNT':
            return
        self.hashKey = Utils.bytesToU32(self.rawData, sfatOffset + 8, self.isLE)
        if self.hashKey == 0x65:
            saht = Saht(hashTableData)
            if saht.valid:
                self.hashTable = saht.hashes
        for i in range(len(self.nodes)):
            self.nodes[i] = SfatNode(Utils.bytesToU32(self.rawData, nodeOffset + (i << 4), self.isLE), None, Utils.bytesToU32(rawData, nodeOffset + (i << 4) + 4, self.isLE), rawData[fileDataOffset + Utils.bytesToU32(rawData, nodeOffset + (i << 4) + 8, self.isLE):fileDataOffset + Utils.bytesToU32(rawData, nodeOffset + (i << 4) + 0xC, self.isLE)])
        self.getFileNames()
        self.valid = True
    def getFileNames(self):
        if self.hashKey == 0x65:
            for i in range(len(self.nodes)):
                if self.nodes[i].hash == 0xEAFDE9E6:
                    additionalSaht = Saht(self.nodes[i].rawData)
                    if additionalSaht.valid:
                        if self.hashTable is None:
                            self.hashTable = additionalSaht.hashes
                        else:
                            self.hashTable.update(additionalSaht.hashes)
                    break
        fileNameOffset = self.sfntOffset + Utils.bytesToU16(self.rawData, self.sfntOffset + 4, self.isLE)
        for i in range(len(self.nodes)):
            if self.nodes[i].attribute & 0x1000000 == 0x1000000:
                curFileNameOffset = (self.nodes[i].attribute & 0xFFFF) << 2
                curFileNameOffset += fileNameOffset
                self.nodes[i].fileName = Utils.bytesToString(self.rawData, curFileNameOffset, None)
            else:
                if not self.hashTable is None:
                    try:
                        self.nodes[i].fileName = self.hashTable[self.nodes[i].hash]
                    except KeyError:
                        self.nodes[i].fileName = None
    def extract(self, destDir):
        try:
            shutil.rmtree(destDir)
        except FileNotFoundError:
            pass
        if destDir[-1] != '/' and destDir[-1] != '\\':
            destDir += '/'
        for i in range(len(self.nodes)):
            if self.nodes[i].fileName == 'HashTable.saht' or self.nodes[i].hash == 0xEAFDE9E6:
                continue
            if not self.nodes[i].save(destDir):
                return False
        return True
    def fromDir(self, srcDir):
        self.isLE = True
        self.emptySfnt = False
        self.hashKey = 0x65
        self.alignment = 0x100
        if srcDir[-1] != '/' and srcDir[-1] != '\\':
            srcDir += '/'
        fileNameList = Utils.makeFileList(srcDir)
        if len(fileNameList) > 0xFFFF:
            return
        self.nodes = list()
        for i in range(len(fileNameList)):
            fileNameList[i] = fileNameList[i][len(srcDir):]
            fileNameList[i] = fileNameList[i].replace('\\', '/')
            curFileData = Utils.fileToBytes(srcDir + fileNameList[i])
            if not curFileData:
                return
            if len(fileNameList[i]) == 10 and fileNameList[i][:2].upper() == '0X':
                try:
                    curHash = int(fileNameList[i], 16)
                    if curHash == 0xEAFDE9E6:
                        continue
                    self.nodes.append(SfatNode(curHash, None, 0, curFileData))
                except ValueError:
                    self.nodes.append(SfatNode(None, fileNameList[i], 0, curFileData))
            else:
                if fileNameList[i] == 'HashTable.saht':
                    continue
                self.nodes.append(SfatNode(None, fileNameList[i], 0, curFileData))
        self.valid = True
    def calcHash(self):
        self.hashTable = dict()
        for i in range(len(self.nodes)):
            if self.nodes[i].hash is None:
                self.nodes[i].hash = 0
                for n in self.nodes[i].fileName.encode():
                    self.nodes[i].hash = n + self.nodes[i].hash * self.hashKey
                    self.nodes[i].hash &= 0xFFFFFFFF
            if self.emptySfnt and self.hashKey == 0x65 and (not self.nodes[i].fileName is None):
                self.hashTable[self.nodes[i].hash] = self.nodes[i].fileName
    def save(self):
        self.calcHash()
        if self.emptySfnt and self.hashKey == 0x65 and len(self.hashTable) > 0:
            self.hashTable[0xEAFDE9E6] = 'HashTable.saht'
            hashTable = Saht(self.hashTable)
            self.nodes.append(SfatNode(0xEAFDE9E6, 'HadhTable.saht', 0, hashTable.save()))
        #ハッシュ値でnodesをバブルソート
        for i in range(len(self.nodes)):
            for j in range(len(self.nodes)-1, i, -1):
                if self.nodes[j].hash < self.nodes[j - 1].hash:
                    self.nodes[j], self.nodes[j - 1] = self.nodes[j - 1], self.nodes[j]
        curFileOffset = 0
        curFileNameOffset = 0
        for i in range(len(self.nodes)):
            self.nodes[i].offset = curFileOffset
            self.nodes[i].end = curFileOffset + len(self.nodes[i].rawData)
            curFileOffset = math.ceil(self.nodes[i].end / self.alignment) * self.alignment
            if (not self.nodes[i].fileName is None) and (not self.emptySfnt):
                self.nodes[i].attribute = 0x1000000 | (curFileNameOffset >> 2)
                curFileNameOffset += len(self.nodes[i].fileName)
                curFileNameOffset += 1
                curFileNameOffset = math.ceil(curFileNameOffset / 4) * 4
        fileData = bytearray(curFileOffset)
        sfntFrontSize = 0x20 + (len(self.nodes) << 4)
        sfntSize = math.ceil((sfntFrontSize + 8 + curFileNameOffset) / self.alignment) * self.alignment
        sfntSize -= sfntFrontSize
        sfnt = bytearray(sfntSize)
        Utils.stringToBytes(sfnt, 0, 4, 'SFNT')
        Utils.U16ToBytes(sfnt, 4, 8, self.isLE)
        sfat = bytearray(0xC + (len(self.nodes) << 4))
        Utils.stringToBytes(sfat, 0, 4, 'SFAT')
        Utils.U16ToBytes(sfat, 4, 0xC, self.isLE)
        Utils.U16ToBytes(sfat, 6, len(self.nodes), self.isLE)
        Utils.U32ToBytes(sfat, 8, self.hashKey, self.isLE)
        for i in range(len(self.nodes)):
            Utils.memcpy(fileData, self.nodes[i].offset, self.nodes[i].rawData, 0, len(self.nodes[i].rawData))
            if (not self.nodes[i].fileName is None) and (not self.emptySfnt):
                Utils.stringToBytes(sfnt, 8 + ((self.nodes[i].attribute & 0xFFFF) << 2), None, self.nodes[i].fileName)
            Utils.U32ToBytes(sfat, 0xC + (i << 4), self.nodes[i].hash, self.isLE)
            Utils.U32ToBytes(sfat, 0xC + (i << 4) + 4, self.nodes[i].attribute, self.isLE)
            Utils.U32ToBytes(sfat, 0xC + (i << 4) + 8, self.nodes[i].offset, self.isLE)
            Utils.U32ToBytes(sfat, 0xC + (i << 4) + 0xC, self.nodes[i].end, self.isLE)
        sarcHead = bytearray(0x14)
        Utils.stringToBytes(sarcHead, 0, 4, 'SARC')
        Utils.U16ToBytes(sarcHead, 4, 0x14, self.isLE)
        Utils.U16ToBytes(sarcHead, 6, 0xFEFF, self.isLE)
        Utils.U32ToBytes(sarcHead, 8, 0x14 + len(sfat) + len(sfnt) + len(fileData), self.isLE)
        Utils.U32ToBytes(sarcHead, 0xC, 0x14 + len(sfat) + len(sfnt), self.isLE)
        Utils.U16ToBytes(sarcHead, 0x10, 0x100, self.isLE)
        return sarcHead + sfat + sfnt + fileData