from hashlib import md5 #, sha256
import struct
import inspect

defaultInputKey = "inputKey"
endian = "little"
hashFunc = md5
debug = False

def doubleHash(input, size=8) -> bytearray:
    md5String = hashFunc(asAscii(input)).digest()
    round1 = bytearray(64)
    for i in range(0, 0x10):
        hexStringOfMd5Byte = bytearray(2)
        md5Entry = asAscii(format(md5String[i], "x"))
        hexStringOfMd5Byte[0:len(md5Entry)] = md5Entry

        if (len(md5Entry) == 1):
            hexStringOfMd5Byte[1] = hexStringOfMd5Byte[0]
        if (i < 1):
            round1[0:2] = hexStringOfMd5Byte
        else:
            concat = (asString(round1) + asString(hexStringOfMd5Byte))
            round1[0:len(concat)] = asAscii(concat)

    md5String = hashFunc(asAscii(asString(round1))).digest()
    round2 = bytearray(64)
    for i in range(0, 0x10):
        hexStringOfMd5Byte = bytearray(2)
        md5Entry = asAscii(format(md5String[i], "x"))
        hexStringOfMd5Byte[0:len(md5Entry)] = md5Entry
        if (len(md5Entry) == 1):
            hexStringOfMd5Byte[1] = hexStringOfMd5Byte[0]
        if (i < 1):
            round2[0:2] = hexStringOfMd5Byte
        else:
            concat = asString(round2) + asString(hexStringOfMd5Byte)
            round2[0:len(concat)] = asAscii(concat)  

    round3 = bytearray(64)
    for i in range(0, size):
        round3[i] = round2[i * 3]

    return round3


def mod3KeyGenerator(seed: int):
    round4 = [0] * 16
    found0s = 0
    found1s = 0
    found2s = 0
    while(found0s == 0 or found1s == 0 or found2s == 0):
        found0s = 0
        found1s = 0
        found2s = 0
        powerOf2 = 1
        seed = seed + 1
        for i in range(0, 10):
            round4[i] = seed % (powerOf2 * 3) // powerOf2
            if (round4[i] == 1):
                found1s = found1s + 1
            elif (round4[i] == 2):
                found2s = found2s + 1
            else:
                found0s = found0s + 1

            powerOf2 = powerOf2 << 1
    
    return (seed, round4)

ended = True

def asInt(bytes:  bytes, start: int = 0) -> int:
    global endian
    if (endian == "big"):
        return struct.unpack_from(">I", bytes, start)[0]
    else:
        return struct.unpack_from("<I", bytes, start)[0]

def assignInt(var: bytearray, start: int, val: int):
    global endian
    if (endian == "big"):
        struct.pack_into(">I", var, start, val)
    else:
        struct.pack_into("<I", var, start, val)

def uppercaseBytearray(byteArray: bytearray):
    uppercase = asAscii(asString(byteArray).upper())
    byteArray = bytearray(64)
    byteArray[0:len(uppercase)] = uppercase
    return byteArray

def asAscii(string: str) -> bytes:
    return string.encode("ascii")

def asString(bytes: bytes) -> str:
    return bytes.decode("ascii").rstrip("\x00")

def asChar(string: str) -> int:
    return asAscii(string)[0]


keyStr1 = asAscii("IO")
keyStr2 = asAscii("lo")
keyStr3 = asAscii("10")
valStr = asAscii("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz0123456789ABCDEF")
offset1 = 0x8 
offset2 = 0x20

def zcfgBeCommonGenKeyBySerialNumMethod3(serialNumber):
    round3 = doubleHash(serialNumber, 10)
    round3 = uppercaseBytearray(round3)
    md5String = hashFunc(asAscii(serialNumber)).digest()
    strAsInt = (md5String[1] << 8) + md5String[2]  
    (strAsInt, round4) = mod3KeyGenerator(strAsInt)
    for i in range(10):
        if (round4[i] == 1):
            newVal = (((round3[i] % 0x1a) * 0x1000000) >> 0x18) + asChar('A')
            round3[i] = newVal
            for j in range(2):
                if (round3[i] == keyStr1[j]):
                    index = offset1 + ((strAsInt + j) % 0x18)
                    round3[i] = valStr[index]
                    break
        elif (round4[i] == 2):
            newVal = (((round3[i] % 0x1a) * 0x1000000) >> 0x18) + asChar('a')
            round3[i] = newVal
            for j in range(2):
                if (round3[i] == keyStr2[j]):
                    index = offset2 + ((strAsInt + j) % 0x18)
                    round3[i] = valStr[index]
                    break
        else:
            newVal = (((round3[i] % 10) * 0x1000000) >> 0x18) + asChar('0')
            # dprint("3: {} - {}".format(round3[i], format(newVal, "c")))
            round3[i] = newVal
            for j in range(2):
                if (round3[i] == keyStr3[j]):
                    var = ((strAsInt + j) >> 0x1f) >> 0x1d
                    index = ((strAsInt + j + var) & 7) - var
                    round3[i] = valStr[index]
                    break

    return asString(round3[0:10])


ser=input('Input serial number:')
print('root password is:')
print(zcfgBeCommonGenKeyBySerialNumMethod3(ser))

