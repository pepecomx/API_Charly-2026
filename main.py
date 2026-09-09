# https://www.youtube.com/watch?v=N5VjIqAsDQ8&t=498s


from fastapi import FastAPI
#from router.router import user
from router.router import dispositivoAPI
#from router.auth import auth_routes
#from dotenv import load_dotenv



app=FastAPI()
#load_dotenv()

#app.include_router(user)
app.include_router(dispositivoAPI)


