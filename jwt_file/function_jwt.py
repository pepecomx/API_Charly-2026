from jwt import encode, decode
from jwt import exceptions
from datetime import datetime, timedelta
#from os import getenv
from fastapi.responses import JSONResponse



def expire_date(days: int):
    date = datetime.now()
    new_date = date + timedelta(days)
    #print(new_date)
    return new_date

def write_token(data: dict):
    print(data)
    #data={**data,"exp":expire_date(2).strftime("%m/%d/%Y, %H:%M:%S")}
    data={**data,"exp":expire_date(2)}
    print(data)
    token = encode(payload=data, key="SECRET", algorithm="HS256")
    #print(token)
    return token


def validate_token(token, output=False):
    print(token)
    try:
        if output:
            #return decode(token, key=getenv("SECRET"), algorithms=["HS256"])           
            return decode(token, key="SECRET", algorithms=["HS256"])
        decode(token, key="SECRET", algorithms=["HS256"])
    except exceptions.DecodeError:
        return JSONResponse(content={"message": "Invalid Token"}, status_code=401)
    except exceptions.ExpiredSignatureError:
        return JSONResponse(content={"message": "Token Expired"}, status_code=401)
    

def writeFile(usuario:str,fecha:str,message:str):
#def writeFile(message:str):
    with open('logApi.txt', 'a') as the_file:
        the_file.write(usuario+"_" + fecha+"_" + message + '\n')


'''
def writeFile(message:str):
    with open('logApi.txt', 'a') as the_file:
        the_file.write(message + '\n')

'''
""" 
from asyncio import exceptions
from base64 import decode
from email.utils import encode_rfc2231
from urllib import response
from jwt import encode,decode
#from jwt import exeptions
from os import getenv
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse



def expire_date(days:int):
    now=datetime.now()
    new_date= now + timedelta(days)
    return new_date
    
        
def write_token(data:dict):
   token=encode(payload={**data},"SECRET",algorithm="HS256")
    #token= encode({"some": "payload"}, "secret", algorithm="HS256")
    
    #token=encode(payload={**data,"exp":expire_date(2)},
    #             key=getenv("SECRET"),algorithm="HS256")
    
    #token=encode(payload={**data,"exp":expire_date(2)},
    #             key=getenv("SECRET"),algorithm="HS256")
    
    return token
    #return token.encode("UTF-8")
    
def validate_token(token,output=False):
    try:
        if output:
            return decode(token,key=getenv("SECRET"),algorithms=["HS256"])
        decode(token,key=getenv("SECRET"),algorithms=["HS256"])
                
    
    except exceptions.DecodeError:
        return JSONResponse(content={"message":"Invalid Token"},status_code=401 ) 
    except exceptions.ExpiredSignatureError:
        return JSONResponse(content={"message":"Token Expired"},status_code=401 ) 
    
    
 """