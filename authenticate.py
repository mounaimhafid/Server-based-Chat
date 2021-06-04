
import hashlib as hsh
from Crypto.Cipher import AES
import hmac
import base64

"""
A3 authentication algorithm: SHA256

INPUT: two integers used for hashing

OUTPUT: string that is a hashing of the two integers (integers were converted to strings)

CALL: authenticate(int1, int2)
 -------> For our purposes int1 is a number generated randomly from the server (this number also sent to client),
          and int2 is the client's 'secret key' that is stored in the server
"""



def authenticate(random, client_key):

    sha = hsh.sha256() #hashing object

    #generate key using arguments
    sha.update(str(random).encode('ascii') + str(client_key).encode('ascii'))
    #print(str(sha.hexdigest()))
    return str(sha.hexdigest())


#authenticate(456789, 7813678)

"""
A8 Key Encryption Algorithm: AES

INPUT: randomly generated number and client_key

OUTPUT: cipher key

-------> To actually use this cipher key, use <cipherKeyName>.encrypt(message) 
         and <cipherKeyName>.decrypt(message)


"""

def generateKey(random, client_key):

    key = authenticate(random, client_key) #key generated using SHA256 algorithm
    iv = b"78951REHR56458" #random iv

    base64.b64encode(key).decode()

    #generate key and return key
    cipher_key = AES.new(key, AES.MODE_CFB, iv)
    return cipher_key



