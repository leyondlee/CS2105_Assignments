import sys
import socket
import zlib

SEQNUM_LENGTH = 4
HASNEXTBIT_LENGTH = 1
CHECKSUM_LENGTH = 8
MAX_PAYLOAD_LENGTH = 64
MAX_PAYLOAD_DATA_LENGTH = MAX_PAYLOAD_LENGTH - SEQNUM_LENGTH - HASNEXTBIT_LENGTH - CHECKSUM_LENGTH - 3
WAIT_TIMEOUT = 0.01

SERVER_ADDRESS = ''
SERVER_PORT = None
SERVER_SOCKET = None

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
    checksumStr = hex(checksum)[2:]
    leadingZeros = CHECKSUM_LENGTH - len(checksumStr)
    for i in range(leadingZeros):
        checksumStr = '0' + checksumStr

    return checksumStr

def processPayloadData(data, expectedSeqNum):
    payloadStr = data.decode()
    payloadSplit = payloadStr.split('|', 4)
    if len(payloadSplit) != 4:
        return None
        
    seqNumHex = payloadSplit[0]
    hasNextBit = payloadSplit[1]
    checksum = payloadSplit[2]
    dataStr = payloadSplit[3]
    seqNum = hexToInt(seqNumHex)
    if seqNum != expectedSeqNum or getChecksumHex(dataStr) != checksum:
        return None
        
    return (seqNum, (hasNextBit == '1'), checksum, dataStr)

def recvMessage(expectedSeqNum):
    global SERVER_SOCKET

    payloadData, client = SERVER_SOCKET.recvfrom(MAX_PAYLOAD_LENGTH)
    processedPayload = processPayloadData(payloadData, expectedSeqNum)
    if processedPayload is None:
        sendAck(client, expectedSeqNum)
        return None
        
    hasNext = processedPayload[1]
    dataStr = processedPayload[3]
    return (dataStr, hasNext, client)
    
def createAckPayload(seqNum):
    seqNumHex = toHex(seqNum, SEQNUM_LENGTH)
    dataStr = 'ACK {}'.format(seqNumHex)
    checksum = getChecksumHex(dataStr)
    payloadStr = '{}|{}'.format(checksum, dataStr)
    return payloadStr.encode()
    
def sendAck(client, seqNum):
    global SERVER_SOCKET
    
    payloadData = createAckPayload(seqNum)
    #print('Sending: {}'.format(payloadData.decode()))
    SERVER_SOCKET.sendto(payloadData, client)
    
def writeToStdout(data):
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

def main():
    global SERVER_PORT, SERVER_SOCKET
    
    argv = sys.argv
    if len(argv) <= 1:
        sys.exit(1)

    port = None
    try:
        port = int(argv[1])
    except:
        sys.exit(1)
    SERVER_PORT = port
        
    SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SERVER_SOCKET.bind(('', SERVER_PORT))
    
    seqNum = 0
    try:
        while True:
            message = ''
            isReceiving = True
            while isReceiving:
                result = recvMessage(seqNum)
                #print(result)
                if result is None:
                    continue
                
                seqNum += len(result[0])
                message += result[0]
                #print('message = {}'.format(message))
                
                hasNext = result[1]
                client = result[2]
                timeout = False
                while hasNext and not timeout:
                    try:
                        SERVER_SOCKET.settimeout(WAIT_TIMEOUT)
                        
                        result = recvMessage(seqNum)
                        if result is None:
                            continue
                            
                        seqNum += len(result[0])
                        message += result[0]
                        
                        hasNext = result[1]
                        client = result[2]
                    except socket.timeout:
                        #print('Timeout')
                        timeout = True
                        
                SERVER_SOCKET.settimeout(None)
                sendAck(client, seqNum)
                #print('Send ACK {}'.format(seqNum))
                
                if not hasNext:
                    isReceiving = False
            
            #print('output = {}'.format(message), file=sys.stderr)
            writeToStdout(message.encode())
            message = ''
    except KeyboardInterrupt:
        pass
        
    SERVER_SOCKET.close()

if __name__ == '__main__':
    main()