import utils, sarc, libyaz0, sys, os
Utils = utils.Utils
Sarc = sarc.Sarc

if len(sys.argv) >= 3:
    cmd = sys.argv[1].upper()
    usedArgs = [False] * len(sys.argv)
    for i in range(3):
        usedArgs[i] = True
    src = sys.argv[2]
    dest = None
    compression = False
    if cmd == 'X':
        srcData = Utils.fileToBytes(src)
        hashTableFile = os.path.dirname(__file__) + '/HashTable.saht'
        hashTableData = Utils.fileToBytes(hashTableFile)
        if not srcData:
            print('Cannnot open ' + src)
            exit()
        if not hashTableData:
            print('Cannnot open ' + hashTableFile)
            exit()
        try:
            decompressData = libyaz0.decompress(srcData)
            srcData = decompressData
        except ValueError:
            pass
        arc = Sarc(srcData, hashTableData)
        if not arc.valid:
            print('Invalid file')
            exit()
    else:
        arc = Sarc(src, None)
        if not arc.valid:
            print('Cannnot open ' + src)
            exit()
    i = 3
    while i < len(sys.argv) - 1:
        if sys.argv[i].upper() == '--BYTEORDER' or sys.argv[i].upper() == '-BO':
            usedArgs[i] = True
            usedArgs[i + 1] = True
            if sys.argv[i + 1].upper() == 'BE':
                arc.isLE = False
        if sys.argv[i].upper() == '--EMPTYSFNT':
            usedArgs[i] = True
            usedArgs[i + 1] = True
            if sys.argv[i + 1].upper() == 'TRUE' or sys.argv[i + 1].upper() == 'ON':
                arc.emptySfnt = True
        if sys.argv[i].upper() == '--ALIGNMENT':
            usedArgs[i] = True
            usedArgs[i + 1] = True
            try:
                alignment = int(sys.argv[i + 1], 16)
                arc.alignment = alignment
            except ValueError:
                pass
        if sys.argv[i].upper() == '--COMPRESSION' or sys.argv[i].upper() == '-C':
            usedArgs[i] = True
            usedArgs[i + 1] = True
            if sys.argv[i + 1].upper() == 'YAZ0':
                compression = 0
            elif sys.argv[i + 1].upper() == 'YAZ1':
                compression = 1
            else:
                compression = None
        i += 1
    for i in range(len(sys.argv)):
        if not usedArgs[i]:
            dest = sys.argv[i]
            break
    if dest is None:
        destSrc, ext = os.path.splitext(src)
        if cmd == 'X':
            dest = destSrc + '.d'
        else:
            if destSrc[-1] == '/' or destSrc[-1] == '\\':
                destSrc = destSrc[:-1]
            dest = destSrc + '.sarc'
    if cmd == 'X':
        if not arc.extract(dest):
            print('An error has occured while extracting')
    else:
        if compression == False:
            fn, ext = os.path.splitext(dest)
            if ext.upper() == '.YAZ0' or ext.upper() == '.SZS':
                compression = 0
            elif ext.upper() == '.YAZ1':
                compression = 1
            else:
                compression = None
        destData = arc.save()
        if not compression is None:
            destData = libyaz0.compress(destData, level=1)
            if compression == 1:
                destData[3] = 0x31
        if not Utils.bytesToFile(destData, dest):
            print('Cannnot open ' + dest)