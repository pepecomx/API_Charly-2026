from datetime import date, datetime
from pydantic  import BaseModel,EmailStr
from typing  import   Optional
from datetime  import  datetime


#class User(BaseModel):
#    username:str
#    email:EmailStr
        
class User(BaseModel):
    id:Optional [int]
    username:str
    email:EmailStr
    passwd:str

class User_Charly(BaseModel):
    IdUsuario:Optional [str]
    NombreUsuario:str
    Contrasena:str
    Token:str
    FechaExpiracion:datetime

    


# esquema general de la tabla 
class UserSchema(BaseModel):
    id: str
    name:str
    user_name:str

    
class DataUser(BaseModel):
    user_name:str
    user_passw:str
    exp:datetime
    
class DataDispositivos (BaseModel):
    IdDispositivo:int
    #IdDispositivo:int
    #IdTipoDispositivo:int
    NombreDispositivo:str
    #MacDispositivo:str
    #Estatus:str
    FechaCreacion:datetime
    
class DataDispositivosVista (BaseModel):
    IdAccion:int
    IdRecurso:int
    NombreRecurso:str
    NombreSeccion:str
    NombreLinea:str
    FechaCreacionRemota:datetime
           