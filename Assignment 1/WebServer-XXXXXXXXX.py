import sys
import socket
import re

BUFFER_SIZE = 1000

def getContentLength(header_string):
    matchObj = re.search(r'Content-Length (\d+)', header_string, flags=re.IGNORECASE)
    if matchObj is None:
        return None
    length_data = int(matchObj.group(1))
    return length_data

def getContentData(client_socket, length):
    length_left = length
    content_data = b''
    while length_left > 0:
        if length_left < BUFFER_SIZE:
            read_size = length_left
        else:
            read_size = BUFFER_SIZE

        data = client_socket.recv(read_size)
        content_data += data
        length_left -= len(data)
    return content_data

def main():
    argv = sys.argv
    if len(argv) <= 1:
        sys.exit(1)

    port = None
    try:
        port = int(argv[1])
    except:
        sys.exit(1)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen()

    keyValueStore = {}
    counterStore = {}

    def handleRequest(header_string, content_data):
        headerSplit = header_string.split(' ')
        method = headerSplit[0].upper()
        path = headerSplit[1]

        pathSplit = path.split('/')[1:]
        pathType = pathSplit[0]
        pathValue = pathSplit[1]

        response = None
        if method == 'GET':
            if pathType == 'key':
                if pathValue in keyValueStore:
                    response = (200, 'OK', keyValueStore[pathValue])
                else:
                    response = (404, 'NotFound', None)
            elif pathType == 'counter':
                if pathValue in counterStore:
                    response = (200, 'OK', str(counterStore[pathValue]).encode())
                else:
                    response = (200, 'OK', b'0')
        elif method == 'POST':
            if pathType == 'key':
                keyValueStore[pathValue] = content_data
                response = (200, 'OK', None)
            elif pathType == 'counter':
                if pathValue not in counterStore:
                    counterStore[pathValue] = 0
                counterStore[pathValue] += 1
                response = (200, 'OK', None)
        elif method == 'DELETE':
            if pathType == 'key':
                if pathType == 'key':
                    if pathValue in keyValueStore:
                        response = (200, 'OK', keyValueStore.pop(pathValue))
                    else:
                        response = (404, 'NotFound', None)

        return response

    try:
        while True:
            client_socket, address = server_socket.accept()

            header_data = b''
            while True:
                data = client_socket.recv(1)
                if len(data) == 0:
                    #print('Closing socket')
                    client_socket.close()
                    break

                header_data += data
                if header_data.endswith(b'  '):
                    header_string = header_data.decode()
                    header_data = b''
                    content_length = getContentLength(header_string)
                    content_data = None
                    if content_length is not None:
                        content_data = getContentData(client_socket, content_length)
                    #print(header_string, content_data)

                    response = handleRequest(header_string, content_data)
                    if response is not None:
                        code = response[0]
                        message = response[1]
                        data = response[2]
                        response_data = None
                        if data is None:
                            response_data = '{} {}  '.format(code, message).encode()
                        else:
                            response_data = '{} {} content-length {}  '.format(code, message, len(data)).encode()
                            response_data += data
                        client_socket.sendall(response_data)
    except KeyboardInterrupt:
        pass

    server_socket.close()

if __name__ == '__main__':
    main()
