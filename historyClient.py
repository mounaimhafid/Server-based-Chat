import time
import socket
import select
import sys
import time
import re
import threading
from chatServices import ChatServices   
global client, message
clientID = 0
destID = 0
receivedEndChat = None

def CONNECTED():
    global client
    client.send('HELLO {0}'.format(clientID))
    print('Connecting to Server...')
    message = client.receive()
    if message == 'CONNECTED':
        print("Client was able to connect\n")
        return True
            
    elif message == 'NOT CONNECTED':
        sys.stdout.write("Client was NOT able to connect")
        sys.stdout.flush()
        return False

#PRINTS MESSAGES RECIEVED
def MESSAGELISTENER(client,destID):
    global receivedEndChat, chatMode
    while True:
        #KEEP RECEIVING MESSAGES
        receivedMessage = client.receive()
        
        #PRINT MESSAGES TO CLIENT
        if receivedMessage != "" and "END_NOTIF" not in receivedMessage.split()[0]:
            print("", end="\r")
            print("Client {0}: {1}".format(destID,receivedMessage))
            print("Client {0}: ".format(clientID), end="")
            sys.stdout.flush()
        
        if "HISTORY_RESP" in receivedMessage.split()[0]:        
             message = protocolMessage.split(',')[1][:-1]
             print(message)

    
#ALLOWS CLIENT TO SEND MESSAGES TO ANOTHER CLIENT
def CHATMODE(client,destID,sessionID):
    global chatMode, receivedEndChat

    print('', end='\r')
    sys.stdout.flush()

    messageListenThread = threading.Thread(target=MESSAGELISTENER, args=(client,destID))
    messageListenThread.start()

    print('\nChat started with client {0}. Type "End Chat" to end.'.format(destID))
    while chatMode:
        messageToSend = input('Client {0}: '.format(clientID))

        if receivedEndChat == True:
            receivedEndChat = False
            break

        if messageToSend.lower().strip() == 'end chat'.lower().strip():
            client.send("END_REQUEST ({0})".format(sessionID))
            chatMode = False
            receivedEndChat = False  # This client caused the chat to end
            break

        if messageToSend.lower().strip() == 'history [0-9]+'.lower().strip():
            client.send("HISTORY_REQ ({0})".format(destID))
            #receive each response (message) in history iteratively

        #SEND MESSAGE TO SERVER SO THAT IT CAN BE FORWARDED TO CLIENT
        client.send('CHAT ({0},{1})'.format(sessionID,messageToSend))

#RETURNS SESSION ID
def getSessionID(ses1,ses2):
    if int(ses1) < int(ses2):
        return str(ses1) + '-' + str(ses2)

    return str(ses2) + '-' + str(ses1)

if __name__ == "__main__":
    global chatMode
    global client
    waiting = False
    chatMode = False
    
    while True:
        #ASK FOR COMMAND
        commands = str(input("Enter a command: "))
        
        #COMMAND FOR LOGGING IN
        if commands.upper() == 'LOGIN':
            clientID = str(input("Enter your desired login ID:"))
        
        #CONNECT CLIENT TO SERVER ** THIS NEEDS INPUT VALIDATION
        client = ChatServices();        
        isConnected = CONNECTED()
        
        #IF THEY ARE CONNECTED BEGIN ASKING FOR MORE COMMANDS
        while isConnected:
            if waiting == False and chatMode == False:
                conn_command = str(input("Enter a command:"))
                #IF USER WANTS TO CHAT REQUEST
                if conn_command.upper() == "CHAT REQUEST":
                    #GET DESTINATION ID AND SEND A REQUEST TO THE SERVER
                    destID = str(input("Enter the client ID you want to connect with: "))
                    client.send('CHAT-REQUEST ' + destID + ' from ' + clientID)
                    #TELL THE USER THAT THEY HAVE TO WAIT FOR RESPONSE
                    print("Wait 10 seconds for client " + destID + " to accept chat request.")
                    time.sleep(10)
                    print("Done waiting")
                    #GET CLIENT RESPONSE FROM SERVER
                    destClientResponse = client.receive()
                    #IF THEY APPROVE THEN SEND A RESPONSE THAT THIS CLIENT HAS READ THE APPROVED AND BEGIN CHAT MODE
                    #NEED A CASE FOR IF THE USER DECLINES
                    if destClientResponse == 'APPROVED':
                        print('Chat request approved! Chat between client ' + str(clientID) + ' (you) and client ' + str(destID) )
                        client.send('APPROVED RECV')
                        chatMode = True
                #EXITS PROGRAM
                elif conn_command.upper() == "EXIT":
                    exit()
                #WAITS FOR A RESPONSE FROM A DIFFERENT CLIENT
                elif conn_command.upper() == "WAIT":
                    waiting = True
                    #SEND A WAITING MESSAGE TO SERVER
                    client.send('WAITING')
                    print("Waiting for 10 seconds...")
                    time.sleep(10)
                    print("Done waiting")
                    #RECIEVE ANY INCOMING CHAT REQUEST
                    msg1 = client.receive()
                    if re.match(r"CHAT-REQUESTED from [0-9]+", msg1):
                        #ASK THE USER IF THEY WANT TO ACCEPT THE CHAT REQUEST
                        #NEED A CASE FOR WHEN THEY SAY NO
                        chat_request_answer = str(input(msg1 + ". Do you accept? "))
                        #IF YES. SEND AN APPROVE MESSAGE TO THE OTHER CLIENT AND BEGIN CHATMODE
                        if chat_request_answer.upper() == "YES":
                            destID = msg1[20]
                            print('Chat request approved! Chat between client ' + str(clientID) + ' (you) and client ' + str(destID))
                            client.send('ACCEPTED')
                            chatMode = True
                    #AFTER WAITING FOR A PERIOD OF TIME STOP WAITING
                    waiting = False
                #FOR BAD COMMANDS
                else:
                    print("INVALID COMMAND. TRY AGAIN")
                
                #IF USERS CHOOSE TO CHAT BEGIN CHAT THREAD
                if chatMode == True:
                    print("Please wait for connection to client")
                    time.sleep(5)
                    sID = getSessionID(clientID, destID)
                    chatModeThread = threading.Thread(target=CHATMODE, args=(client,destID, sID))
                    chatModeThread.start()
