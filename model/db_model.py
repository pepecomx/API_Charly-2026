from sqlalchemy import Table,Column
from sqlalchemy.sql.sqltypes import Integer,String
from config.db import engine,meta_data

# DEFINE una tabla 
users=Table("users",meta_data,
            Column("id",Integer,primary_key=True),
            Column("name",String(255),nullable=False),
            Column("user_name",String(255),nullable=False),
            Column("user_passw",String(255),nullable=False),
            ) 


usuarios_c=Table("usuarios",meta_data,
            Column("IdUsuario",String(255),primary_key=True),
            Column("NombreUsuario",String(255),nullable=False),
            Column("Contrasena",String(255),nullable=False),
            Column("Token",String(255),nullable=False),
            
            Column("FechaExpiracion",String(255),nullable=False),
            
            ) 


dispositivos=Table("dispositivos",meta_data,
            Column("IdDispositivo",Integer,primary_key=True),
           # Column("IdRecurso",Integer,nullable=True),
           # Column("IdTipoDispositivo",Integer,nullable=True),
            Column("NombreDispositivo",String(255),nullable=False),
            #Column("MacDispositivo",String(255),nullable=False),
            #Column("Estatus",Integer,nullable=True),
            #Column("FechaCreacion",String,nullable=True),
            ) 

eventosVista=Table("eventos_vw",meta_data,
            Column("IdAccion",Integer,primary_key=True),
            Column("IdRecurso",Integer,nullable=True),
            Column("NombreRecurso",String(255),nullable=True),
            Column("NombreSeccion",String(255),nullable=True),
            #Column("NombreLinea",String(255),nullable=False),
            #Column("FechaCreacionRemota",String,nullable=True),
            ) 


'''
class DataDispositivosVista (BaseModel):
    IdAccion:int
    IdRecurso:int
    NombreRecurso:str
    NombreSeccion:str
    NombreLinea:str
    #FechaCreacionRemota:date   
'''


#### meta_data.create_all(engine)  # Crea la  tablas 

