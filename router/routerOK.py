
## ----

## charly_API
## @cc3s0V1si0n
## ## uvicorn main:app 

from ast import Try
import string
from unicodedata import name
from urllib import response
from fastapi import APIRouter,Response,Request,Header,Body
from fastapi.responses import HTMLResponse,JSONResponse

from schema.user_schema import UserSchema,DataUser,DataDispositivos,DataDispositivosVista,User,User_Charly
from jwt_file.function_jwt import write_token,validate_token,expire_date,writeFile
from router.local import key

from config.db import engine
from model.db_model import users,dispositivos, eventosVista,usuarios_c
from typing import List

from cryptography.fernet import Fernet

from datetime import datetime, timedelta

#-----

secret_pwd=Fernet(key)
key2=Fernet.generate_key()
secret_Token=Fernet(key2)

dispositivoAPI=APIRouter()


#-----
 ############### _________________________________________________________
# Regresa datos de usuario "IdUsuario"
@dispositivoAPI.put("/api/actualizaContrasena/", status_code=201)

#@dispositivoAPI.put("/api/actualiza_contrasena/{IdUsuario}", status_code=201)
#def actualiza_contrasena(_IdUsuario:str,_contrasenaActual:str,_contrasenaNueva:str):
async def actualiza_contrasena(*,_IdUsuario: str = Body(...),_contrasenaActual: str = Body(...),_contrasenaNueva: str = Body(...)):    
        #print(contrasena_enc)
        #print(contrasena_enc)
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with engine.connect() as conn: 
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()
            contrasena_enc=secret_pwd.encrypt(_contrasenaNueva.encode("utf-8"))
            datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()   
            #c_contrasenaActual_ver=secret_pwd.encrypt(_contrasenaActual.encode("utf-8"))                         
            
            if id!=None:
                print(id)
                # decodifica contraseÃ±a almacenda    
                contrasena_int=secret_pwd.decrypt(datos[2].encode("utf-8"))#print (_contrasena) 
                contrasena_int_s = str(contrasena_int.decode())# elimina caracter  'b   byte
                print(_contrasenaActual)
                print(contrasena_int_s)
                
                if (_contrasenaActual==contrasena_int_s):    
                    contrasena_enc=secret_pwd.encrypt(_contrasenaNueva.encode("utf-8")) 
                    token=secret_Token.encrypt(_contrasenaNueva.encode("utf-8"))
                    #print(contrasena_enc)
                    
                    fecha=expire_date(2)
                    result=conn.execute(usuarios_c.update().values(Contrasena=contrasena_enc).where(usuarios_c.c.IdUsuario == _IdUsuario))
                    result_t=conn.execute(usuarios_c.update().values(Token=token).where(usuarios_c.c.IdUsuario == _IdUsuario))
                    result_f=conn.execute(usuarios_c.update().values(FechaExpiracion=fecha).where(usuarios_c.c.IdUsuario == _IdUsuario))
                                
                    #print(result)
                    #print(result_t)
                    #print(result_f)
                    
                    print("ContraseÃ±a actualizada correctamente")
                    writeFile(_IdUsuario,fecha_y_hora,"actualiza_contrasena:ContraseÃ±a actualizada")
                    return JSONResponse(content={"message":"ContraseÃ±a actualizada correctamente"},status_code=201)   
                else:
                    print("ContraseÃ±a actual no correcta!!")
                    writeFile(_IdUsuario,fecha_y_hora,"actualiza_contrasena:ContraseÃ±a actual no correcta!!")
                    return JSONResponse(content={"message":"ContraseÃ±a actual no correcta!!"},status_code=403)
                
            else:
                print("Usuario no encontrado !!")
                writeFile(_IdUsuario,fecha_y_hora,"actualiza_contrasena:Usuario no encontrado !!")                
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"actualiza_contrasena:Error No identificado!!")                
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 

'''
#-----
 ############### _________________________________________________________
# Regresa datos de usuario "IdUsuario"
@dispositivoAPI.post("/api/obtieneToken/", status_code=201)
#def obtiene_token(_IdUsuario:str,_contrasena:str):
#async def obtiene_token_post(*,_IdUsuario: str = Body(...),_contrasena: str = Body(...)):     
async def obtiene_token(_IdUsuario: str ,_contrasena: str ): 
    print ("obtiene_token" )
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:    
        with engine.connect() as conn: 
            print ("obtiene_token  sigo aqui" )    
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                #contrasena_user=secret_pwd.encrypt(_contrasena.encode("utf-8")) 
                contrasena_int=secret_pwd.decrypt(datos[2].encode("utf-8"))
                
                #print (_contrasena) 
                contrasena_int_s = str(contrasena_int.decode())# elimina caracter  'b   byte
                #print(datos[2])
                #print (contrasena_int_s)
                
                if _contrasena==contrasena_int_s:          
                
                    fecha_hoy=expire_date(0) # fecha de hoy
                    
                    print("FECHAS")
                    print(fecha_hoy)           
                    #print(datos[2])  # contraseÃ±a usuario
                    #print(datos[3])  # token usuario
                    print(datos[4])  # fecha token
                    
                    if (fecha_hoy<=datos[4]):
                        print("TOKEN OK" )
                        print(datos[3])  # token usuario
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Token Enviado")
                        return datos[3]
                    else :
                        print("Token caducado" )
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Token caducado")                        
                        return JSONResponse(content={"message":"Token caducado"},status_code=406)  
                    
                else:
                    print("ContraseÃ±a no correcta")
                    writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:ContraseÃ±a actual no correcta!!")
                    return JSONResponse(content={"message":"ContraseÃ±a actual no correcta!!"},status_code=403)  # 403
            else:
                print("Usuario no encontrado!!")
                writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Usuario no encontrado!!")  
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)  # 404
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Error No identificado!!")  
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 
    finally:
        print ("obtiene_token BD cerrado" )  
        print ("escribiendo archivo" )  
        #writeFile("obtiene_token BD cerrado")
        #with open('somefile.txt', 'a') as the_file:
        #    the_file.write('Hello\n')     
        conn.close()
######## **************************
#$$$$
'''


@dispositivoAPI.get("/api/obtieneToken/", status_code=201)
#def obtiene_token(_IdUsuario:str,_contrasena:str):
#async def obtiene_token_post(*,_IdUsuario: str = Body(...),_contrasena: str = Body(...)):     
async def obtiene_token(_IdUsuario: str ,_contrasena: str ): 
    print ("obtiene_token" )
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:    
        with engine.connect() as conn: 
            print ("obtiene_token  sigo aqui" )    
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                #contrasena_user=secret_pwd.encrypt(_contrasena.encode("utf-8")) 
                contrasena_int=secret_pwd.decrypt(datos[2].encode("utf-8"))
                
                #print (_contrasena) 
                contrasena_int_s = str(contrasena_int.decode())# elimina caracter  'b   byte
                #print(datos[2])
                #print (contrasena_int_s)
                
                if _contrasena==contrasena_int_s:          
                
                    fecha_hoy=expire_date(0) # fecha de hoy
                    
                    print("FECHAS")
                    print(fecha_hoy)           
                    #print(datos[2])  # contraseña usuario
                    #print(datos[3])  # token usuario
                    print(datos[4])  # fecha token
                    
                    if (fecha_hoy<=datos[4]):
                        print("TOKEN OK" )
                        print(datos[3])  # token usuario
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Token Enviado")
                        return datos[3]
                    else :
                        print("Token caducado" )
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Token caducado")                        
                        return JSONResponse(content={"message":"Token caducado"},status_code=406)  
                    
                else:
                    print("Contraseña no correcta")
                    writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Contraseña actual no correcta!!")
                    return JSONResponse(content={"message":"Contraseña actual no correcta"},status_code=401)  # 403
            else:
                print("Usuario no encontrado!!")
                writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Usuario no encontrado!!")  
                return JSONResponse(content={"message":"Usuario no encontrado"},status_code=404)
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"obtiene_token:Error No identificado!!")  
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 
    finally:
        print ("obtiene_token BD cerrado" )  
        print ("escribiendo archivo" )  
        #writeFile("obtiene_token BD cerrado")
        #with open('somefile.txt', 'a') as the_file:
        #    the_file.write('Hello\n')     
        conn.close()
######## **************************

#$$$$$$




'''
#-----
 ############### _________________________________________________________
# Regresa datos de usuario "IdUsuario"


#---
#@dispositivoAPI.put("/api/obtieneToken/", status_code=201)
#async def obtiene_token(*,_IdUsuario: str = Body(...),_contrasena: str = Body(...)):     
@dispositivoAPI.get("/api/obtieneToken_get/{_IdUsuario}/{_contrasena}", status_code=201)
async def obtiene_token_get(_IdUsuario: str ,_contrasena: str ):     

    print ("obtiene_token" )
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:    
        with engine.connect() as conn: 
            print ("obtiene_token  sigo aqui" )    
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                #contrasena_user=secret_pwd.encrypt(_contrasena.encode("utf-8")) 
                contrasena_int=secret_pwd.decrypt(datos[2].encode("utf-8"))
                
                #print (_contrasena) 
                contrasena_int_s = str(contrasena_int.decode())# elimina caracter  'b   byte
                #print(datos[2])
                #print (contrasena_int_s)
                
                if _contrasena==contrasena_int_s:          
                
                    fecha_hoy=expire_date(0) # fecha de hoy
                    
                    print("FECHAS")
                    print(fecha_hoy)           
                    #print(datos[2])  # contraseÃ±a usuario
                    #print(datos[3])  # token usuario
                    print(datos[4])  # fecha token
                    
                    if (fecha_hoy<=datos[4]):
                        print("TOKEN OK" )
                        print(datos[3])  # token usuario
                        return datos[3]
                    else :
                        print("Token caducado" )
                        return JSONResponse(content={"message":"Token caducado"},status_code=404)  
                    
                else:
                    print("ContraseÃ±a no correcta")  
                    return JSONResponse(content={"message":"ContraseÃ±a no correcta!!"},status_code=401)  
            else:
                print("Usuario no encontrado!!")  
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)  
    except: 
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=404) 
    finally:
        print ("obtiene_token BD cerrado" )  
        print ("escribiendo archivo" )  
        writeFile("obtiene_token BD cerrado")
        #with open('somefile.txt', 'a') as the_file:
        #    the_file.write('Hello\n')     
        conn.close()
######## **************************
'''

@dispositivoAPI.put("/api/actualizaToken/", status_code=201)
async def actualiza_token(*,_IdUsuario: str = Body(...),_contrasena: str = Body(...)):     
#async def obtiene_token(_IdUsuario: str ,_contrasena: str ):     

    print ("actualizaToken" )
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:    
        with engine.connect() as conn: 
            print ("obtiene_token  sigo aqui" )    
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                #contrasena_user=secret_pwd.encrypt(_contrasena.encode("utf-8")) 
                contrasena_int=secret_pwd.decrypt(datos[2].encode("utf-8"))
                
                #print (_contrasena) 
                contrasena_int_s = str(contrasena_int.decode())# elimina caracter  'b   byte
                #print(datos[2])
                #print (contrasena_int_s)
                
                if _contrasena==contrasena_int_s:          
                
                    fecha_hoy=expire_date(0) # fecha de hoy
                    
                    print("FECHAS")
                    print(fecha_hoy)           
                    #print(datos[2])  # contraseÃ±a usuario
                    #print(datos[3])  # token usuario
                    print(datos[4])  # fecha token
                    
                    #if (fecha_hoy<=datos[4]):
                    #    print("TOKEN OK" )
                    #    print(datos[3])  # token usuario
                    #    return datos[3]
                    #else :
                    token=secret_Token.encrypt(_contrasena.encode("utf-8"))                        
                    fecha=expire_date(2)
                    #result=conn.execute(usuarios_c.update().values(Contrasena=contrasena_enc).where(usuarios_c.c.IdUsuario == _IdUsuario))
                    result_t=conn.execute(usuarios_c.update().values(Token=token).where(usuarios_c.c.IdUsuario == _IdUsuario))
                    result_f=conn.execute(usuarios_c.update().values(FechaExpiracion=fecha).where(usuarios_c.c.IdUsuario == _IdUsuario))
                
                    print("Token actualizado--actualizaToken" )   
                    writeFile(_IdUsuario,fecha_y_hora,"actualiza_token:Token actualizado")   
                    #return JSONResponse(content={"token":token},status_code=404)  
                    return JSONResponse(content={"message":"Token actualizado"},status_code=404)
		    #return token
                    
                else:
                    print("ContraseÃ±a no correcta")
                    writeFile(_IdUsuario,fecha_y_hora,"actualiza_token:ContraseÃ±a actual no correcta!!")    
                    return JSONResponse(content={"message":"ContraseÃ±a actual no correcta!!"},status_code=403)  
            else:
                print("Usuario no encontrado!!")
                writeFile(_IdUsuario,fecha_y_hora,"actualiza_token:Usuario no encontrado!!")  
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)  
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"actualiza_token:Error No identificado!!") 
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 
    finally:
        print ("obtiene_token BD cerrado" )  
        print ("escribiendo archivo" )  
        #writeFile("obtiene_token BD cerrado")
        #with open('somefile.txt', 'a') as the_file:
        #    the_file.write('Hello\n')     
        conn.close()
######## **************************






 ############### _________________________________________________________
# Regresa datos SOLICITADOS 
# INTEGRA USUARIO y TOKEN
'''
@dispositivoAPI.get("/api/obtieneEventos/{_IdUsuario}/{_token}/{_fecha}", status_code=201)
#@dispositivoAPI.get("/api/obtieneEventos/", status_code=201)
#@dispositivoAPI.get("/api/obtiene_datos_2/{IdUsuario}")
#def obtiene_eventos_get(_IdUsuario:str,_token:str,_fecha:str):
async def obtiene_eventos(_IdUsuario: str , _token:str,_fecha:str):    
#async def obtiene_eventos(*,_IdUsuario: str = Body(...), _token:str= Body(...),_fecha:str= Body(...)):    
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        try:
            #fecha_inicio = datetime.strptime('2022-10-10', '%Y-%m-%d')
            fecha_inicio = str(datetime.strptime(_fecha, '%Y-%m-%d'))
            fecha_fin = str(datetime.strptime(_fecha, '%Y-%m-%d') + timedelta(1))
            print("FECHAS")
            print(fecha_inicio)
            print(fecha_fin)
            #fecha_fin='2022-10-11'
        except: 
            return JSONResponse(content={"message":"Error en fecha!!"},status_code=404) 

        with engine.connect() as conn: 
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                fecha_hoy=expire_date(0) # fecha de hoy
                

                if (fecha_hoy<=datos[4]):
                    print("TOKEN OK" )
                    #print(datos[3])  # token usuario
                    #realiza operacion solicitada 
                    if  (datos[3]== _token):
                        print("TOKENS IGUALES " )
                        
                        #Realiza operacion solicitada
                        with engine.connect() as conn:

                            SQL="SELECT NombreLinea, NombreSeccion, Accion as clasif, hour(FechaCreacionLocal) as hora,FechaCreacionLocal, count(NombreLinea) as cantidad FROM (SELECT * FROM vision.eventos_vw1 WHERE FechaCreacionLocal BETWEEN " + "'" + fecha_inicio + "'" + " AND " + "'" + fecha_fin + "'" + ") as t1 GROUP BY NombreLinea, NombreSeccion, Accion, hour(FechaCreacionLocal)"
                            print(SQL)
                            result = conn.execute(SQL).fetchall()

                            print("Consulta exitosa") 
                            return result
                    
                        # return datos[3]
                    else:
                        print("TOKEN NO VALIDO!! " ) 
                        return JSONResponse(content={"message":"Token no valido!!"},status_code=403)  # 403    
                    
                else :
                    print("Token caducado!!" )
                    return JSONResponse(content={"message":"Token caducado!!"},status_code=406)  # 406
                
            else:
                print("Usuario no correcto!!")  
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)   # 404
    except: 
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500)  #
        
 ######## **************************
 '''

'''
 ############### _________________obtieneEventos_post________________________________________
# Regresa datos SOLICITADOS 
# INTEGRA USUARIO y TOKEN

@dispositivoAPI.post("/api/obtieneEventos/", status_code=201)
#@dispositivoAPI.get("/api/obtieneEventos/", status_code=201)
#@dispositivoAPI.get("/api/obtiene_datos_2/{IdUsuario}")
#def obtiene_eventos(_IdUsuario:str,_token:str,_fecha:str):
async def obtiene_eventos(_IdUsuario: str , _token:str,_fecha:str):    
#async def obtiene_eventos(*,_IdUsuario: str = Body(...), _token:str= Body(...),_fecha:str= Body(...)):    
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        try:
            #fecha_inicio = datetime.strptime('2022-10-10', '%Y-%m-%d')
            fecha_inicio = str(datetime.strptime(_fecha, '%Y-%m-%d'))
            fecha_fin = str(datetime.strptime(_fecha, '%Y-%m-%d') + timedelta(1))
            print("FECHAS")
            print(fecha_inicio)
            print(fecha_fin)
            #fecha_fin='2022-10-11'
        except:
            writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Error en fecha!!")  
            return JSONResponse(content={"message":"Error en fecha!!"},status_code=405) 

        with engine.connect() as conn: 
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                fecha_hoy=expire_date(0) # fecha de hoy
                

                if (fecha_hoy<=datos[4]):
                    print("TOKEN OK" )
                    #print(datos[3])  # token usuario
                    #realiza operacion solicitada 
                    if  (datos[3]== _token):
                        print("TOKENS IGUALES " )
                        
                        #Realiza operacion solicitada
                        with engine.connect() as conn:

                            SQL="SELECT NombreLinea, NombreSeccion, Accion as clasif, hour(FechaCreacionLocal) as hora,FechaCreacionLocal, count(NombreLinea) as cantidad FROM (SELECT * FROM vision.eventos_vw1 WHERE FechaCreacionLocal BETWEEN " + "'" + fecha_inicio + "'" + " AND " + "'" + fecha_fin + "'" + ") as t1 GROUP BY NombreLinea, NombreSeccion, Accion, hour(FechaCreacionLocal)"
                            print(SQL)
                            result = conn.execute(SQL).fetchall()

                            print("Consulta exitosa")
                            writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Consulta exitosa") 
                            return result
                    
                        # return datos[3]
                    else:
                        print("TOKEN NO VALIDO!! " )
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Token no valido!!")   
                        return JSONResponse(content={"message":"Token no valido!!"},status_code=402)      
                    
                else :
                    print("Token caducado!!" )
                    writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Token caducado!!") 
                    return JSONResponse(content={"message":"Token caducado!!"},status_code=406)  
                
            else:
                print("Usuario no correcto!!")
                writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Usuario no encontrado!!")       
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)  
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Error No identificado!!")     
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 
        
 ######## **************************
 

#$$$$$$
'''

 ############### _________________obtieneEventos_get________________________________________
# Regresa datos SOLICITADOS 
# INTEGRA USUARIO y TOKEN

@dispositivoAPI.get("/api/obtieneEventos/", status_code=201)
async def obtiene_eventos(_IdUsuario: str , _token:str,_fecha:str):    
    fecha_y_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        try:
            #fecha_inicio = datetime.strptime('2022-10-10', '%Y-%m-%d')
            fecha_inicio = str(datetime.strptime(_fecha, '%Y-%m-%d'))
            fecha_fin = str(datetime.strptime(_fecha, '%Y-%m-%d') + timedelta(1))
            print("FECHAS")
            print(fecha_inicio)
            print(fecha_fin)
            #fecha_fin='2022-10-11'
        except:
            writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Error en fecha!!")  
            return JSONResponse(content={"message":"Error en fecha!!"},status_code=405) 

        with engine.connect() as conn: 
            id=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()       
        
            if id!=None:
                datos=conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()                    
                fecha_hoy=expire_date(0) # fecha de hoy
                

                if (fecha_hoy<=datos[4]):
                    print("TOKEN OK" )
                    #print(datos[3])  # token usuario
                    #realiza operacion solicitada 
                    if  (datos[3]== _token):
                        print("TOKENS IGUALES " )
                        
                        #Realiza operacion solicitada
                        with engine.connect() as conn:

                            SQL="SELECT NombreLinea, NombreSeccion, Accion as clasif, hour(FechaCreacionLocal) as hora,FechaCreacionLocal, count(NombreLinea) as cantidad FROM (SELECT * FROM vision.eventos_vw1 WHERE FechaCreacionLocal BETWEEN " + "'" + fecha_inicio + "'" + " AND " + "'" + fecha_fin + "'" + ") as t1 GROUP BY NombreLinea, NombreSeccion, Accion, hour(FechaCreacionLocal)"
                            print(SQL)
                            result = conn.execute(SQL).fetchall()

                            print("Consulta exitosa")
                            writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Consulta exitosa") 
                            return result
                    
                        # return datos[3]
                    else:
                        print("TOKEN NO VALIDO!! " )
                        writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Token no valido!!")   
                        return JSONResponse(content={"message":"Token no valido!!"},status_code=402)      
                    
                else :
                    print("Token caducado!!" )
                    writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Token caducado!!") 
                    return JSONResponse(content={"message":"Token caducado!!"},status_code=406)  
                
            else:
                print("Usuario no correcto!!")
                writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Usuario no encontrado!!")       
                return JSONResponse(content={"message":"Usuario no encontrado!!"},status_code=401)  
    except: 
        writeFile(_IdUsuario,fecha_y_hora,"obtiene_eventos:Error No identificado!!")     
        return JSONResponse(content={"message":"Error No identificado!!"},status_code=500) 
        
 ######## **************************
 

#$$$$$
