import sys

BUFFER_SIZE = 1000

def writeToStdout(data):
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

def processPacket(size):
    sizeRead = 0
    while sizeRead < size:
        sizeLeft = size - sizeRead
        if sizeLeft > BUFFER_SIZE:
            readSize = BUFFER_SIZE
        else:
            readSize = sizeLeft
        data = sys.stdin.buffer.read1(readSize)
        sizeRead += len(data)
        writeToStdout(data)

def getSizeFromHeader(data):
    data_split = data.split(b' ')
    size_data = data_split[1][:-1]
    return int(size_data.decode())

def main():
    header_data = None
    run = True
    while run:
        data = sys.stdin.buffer.read1(1)
        if len(data) == 0:
            run = False
            continue

        if not header_data:
            header_data = bytes()
        header_data += data

        if data == b'B':
            size = getSizeFromHeader(header_data)
            header_data = None
            processPacket(size)

if __name__ == '__main__':
    main()
