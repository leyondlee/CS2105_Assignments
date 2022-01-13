import sys
import zlib
import socket

SEQNUM_LENGTH = 4
HASNEXTBIT_LENGTH = 1
CHECKSUM_LENGTH = 8
MAX_PAYLOAD_LENGTH = 64
MAX_PAYLOAD_DATA_LENGTH = MAX_PAYLOAD_LENGTH - SEQNUM_LENGTH - HASNEXTBIT_LENGTH - CHECKSUM_LENGTH - 3
WINDOW_SIZE = 5
ACK_TIMEOUT = 0.05

SERVER_ADDRESS = 'localhost'
SERVER_PORT = None
SERVER_SOCKET = None
CLIENT_SOCKET = None

def toHex(num, minLength):
    hexResult = hex(num)[2:]
    leadingZeros = minLength - len(hexResult)
    for i in range(leadingZeros):
        hexResult = '0' + hexResult
        
    return hexResult
    
def hexToInt(hexStr):
    try:
        num = int(hexStr, 16)
    except ValueError:
        num = None
        
    return num

def getChecksumHex(dataStr):
    global CHECKSUM_LENGTH

    checksum = zlib.crc32(dataStr.encode())
    checksumStr = toHex(checksum, CHECKSUM_LENGTH)

    return checksumStr

def createPayload(seqNum, hasNext, dataStr):
    seqNumHex = toHex(seqNum, SEQNUM_LENGTH)
    hasNextBit = (1 if hasNext else 0)
    checksumStr = getChecksumHex(dataStr)
    payloadStr = '{seq}|{hasNext}|{checksum}|{data}'.format(seq=seqNumHex, hasNext=hasNextBit, checksum=checksumStr, data=dataStr)
    return payloadStr.encode()

def sendMessage(message, seqNum):
    global CLIENT_SOCKET, MAX_PAYLOAD_DATA_LENGTH

    if CLIENT_SOCKET is None:
        return None

    #print('Payloads for "{}"'.format(message))
    messagePayloadList = []
    while message:
        size = len(message)
        if size > MAX_PAYLOAD_DATA_LENGTH:
            payloadLength = MAX_PAYLOAD_DATA_LENGTH
        else:
            payloadLength = size
        messagePayloadList.append(message[:payloadLength])
        message = message[payloadLength:]
    
    while messagePayloadList:
        count = 0
        buffer = []
        while count < WINDOW_SIZE and messagePayloadList:
            dataStr = messagePayloadList.pop(0)
            if messagePayloadList:
                hasNext = True
            else:
                hasNext = False
            payloadData = createPayload(seqNum, hasNext, dataStr)
            buffer.append([seqNum,payloadData])
            seqNum += len(dataStr)
            count += 1
            
        for i in range(count):
            CLIENT_SOCKET.sendto(buffer[i][1], (SERVER_ADDRESS, SERVER_PORT))
        
        largestAckNum = 0
        hasUnAck = True
        while hasUnAck:
            ackSeqNum = recvAck()
            if ackSeqNum is not None and ackSeqNum > largestAckNum:
                #print('Received: ACK {}'.format(ackSeqNum))
                largestAckNum = ackSeqNum
            
            curUnAckPayload = None
            for i in range(count):
                if buffer[i][0] >= largestAckNum:
                    curUnAckPayload = buffer[i][1]
                    break
            
            if curUnAckPayload is None:
                hasUnAck = False
            else:
                CLIENT_SOCKET.sendto(curUnAckPayload, (SERVER_ADDRESS, SERVER_PORT))
                
    return seqNum
    
def recvAck():
    global CLIENT_SOCKET
    
    try:
        ackData, server = CLIENT_SOCKET.recvfrom(MAX_PAYLOAD_LENGTH)
    except socket.timeout:
        #print('Timeout')
        return None
        
    #print('Received: {}'.format(ackData.decode()))
        
    ackStr = ackData.decode()
    #print(ackStr)
    ackSplit = ackStr.split('|', 2)
    if len(ackSplit) != 2:
        return None
        
    checksum = ackSplit[0]
    dataStr = ackSplit[1]
    if getChecksumHex(dataStr) != checksum:
        return None
        
    dataStrSplit = dataStr.split(' ',2)
    if len(dataStrSplit) != 2 or dataStrSplit[0] != 'ACK':
        return None
        
    ackSeqNum = hexToInt(dataStrSplit[1])
    if ackSeqNum is None:
        return None
        
    #print('ackSeqNum = {}'.format(ackSeqNum))
        
    return ackSeqNum

def main():
    global SERVER_PORT, CLIENT_SOCKET

    argv = sys.argv
    if len(argv) <= 1:
        sys.exit(1)

    port = None
    try:
        port = int(argv[1])
    except:
        sys.exit(1)
    SERVER_PORT = port
    
    CLIENT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    CLIENT_SOCKET.settimeout(ACK_TIMEOUT)
    
    seqNum = 0
    try:
        isRunning = True
        while isRunning:
            message = ''
            isReading = True
            while isReading:
                line = sys.stdin.readline()
                if len(line) == 0:
                    isReading = False
                
                message += line
                if len(message) >= (MAX_PAYLOAD_DATA_LENGTH * WINDOW_SIZE):
                    isReading = False
                    
            if not message:
                isRunning = False
                continue
            
            seqNum = sendMessage(message, seqNum)
    except KeyboardInterrupt:
        pass

    CLIENT_SOCKET.close()

if __name__ == '__main__':
    main()