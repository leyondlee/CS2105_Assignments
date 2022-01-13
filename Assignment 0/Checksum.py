import argparse
import zlib
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')

    args = parser.parse_args()
    filename = args.filename
    if not os.path.isfile(filename):
        return
        
    with open(filename,'rb') as file:
        data = file.read()
    checksum = zlib.crc32(data)
    print(checksum)
    
if __name__ == '__main__':
    main()
