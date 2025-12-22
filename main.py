from fastapi import FastAPI, Form, Request, Response, Cookie,status,Query
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from upstash_redis import Redis
import psycopg
import bcrypt
import os 
import secrets
import string
import random
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
import urllib.parse  
import json
import requests
from pydantic import BaseModel
import time
import uvicorn
from pymongo import MongoClient
import certifi

app = FastAPI(
    title="AH Gambling",
    description="AH Gambling",
    version="1.0.0",
)

def getMongoClient(ConnectionURI = None):
    if not ConnectionURI:
        ConnectionURI = "mongodb+srv://gamblesite_db_user:VQKwxemda7DhocAi@gamblesite.ttpjfpf.mongodb.net/gamblesite?retryWrites=true&w=majority&appName=gamblesite"
    client = MongoClient(
        ConnectionURI,
        serverSelectionTimeoutMS=20000,
        tls=True,
        tlsCAFile=certifi.where()
    )
    return client

Mongo_Client = getMongoClient()

def getMainMongo():
    db = Mongo_Client["main"]
    collection = db["main"]
    return {"db": db,"collection":collection}


class deposit(BaseModel):
    robloxusername: str
    siteusername : str
    sessionid : str
    amount : int
    success : bool

class MinesClick(BaseModel):
    tileIndex: int

redis = Redis(
    url=os.environ["REDIS_URL"],
    token=os.environ["REDIS_TOKEN"]
)

templates = Jinja2Templates(directory="templates")

def CheckIfUserIsLoggedIn(request,htmlfile,htmlfile2):
    SessionId = request.cookies.get('SessionId')  
    if not SessionId:
        return templates.TemplateResponse(htmlfile, {"request": request})
    else:
        try:
            with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:

                with conn.cursor() as cursor:
                    cursor.execute("SELECT sessionid FROM accounts WHERE sessionid = %s", (SessionId,))
                    
                    result = cursor.fetchone()  
                    
                    if result and result[0] == SessionId:
                        return templates.TemplateResponse(htmlfile2, {"request": request})
                    else:
                        response = templates.TemplateResponse(htmlfile, {"request": request})
                        response.delete_cookie("SessionId")
                        return response
        
        except Exception as error:
            return templates.TemplateResponse(
                htmlfile,
                {"request": request, "error": f"Database error: {error}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@app.get("/register", response_class=HTMLResponse)
def readregister(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","home.html")


@app.get("/login",response_class =  HTMLResponse)
def readlogin(request: Request):
    SessionId = request.cookies.get('SessionId')  
    if not SessionId:
        return templates.TemplateResponse("login.html", {"request": request})
    else:
        try:
            with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:

                with conn.cursor() as cursor:
                    cursor.execute("SELECT sessionid FROM accounts WHERE sessionid = %s", (SessionId,))
                    
                    result = cursor.fetchone()  
                    
                    if result and result[0] == SessionId:
                        return templates.TemplateResponse("home.html", {"request": request})
                    else:
                        response = templates.TemplateResponse("login.html", {"request": request})
                        response.delete_cookie("SessionId")
                        return response
        
        except Exception as error:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": f"Database error: {error}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
@app.get("/mines",response_class =  HTMLResponse)
def loadmines(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","mines.html")


@app.get("/towers",response_class =  HTMLResponse)
def towers(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","towers.html")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","home.html")

@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/cookie/set")
def set_cookie():
    ten_years = 10 * 365 * 24 * 60 * 60
    response = Response(content="Cookie set!")
    response.set_cookie(
        key="SessionId",
        value="cookie_value",
        max_age=ten_years,
        expires=ten_years,
        httponly=True,
        path="/"
    )
    return response  

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="SessionId")
    return response


@app.get("/getbalance")
def get(SessionId: str = Cookie(None)):
    mainMongo = getMainMongo()
    mainCollection = mainMongo["collection"]

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
                result = cursor.fetchone()  
                if not result:
                    return {"error": "Session not found"}
                username = result[0]
    except Exception as error:
        return {"error": str(error)}
    

    try:
        doc = mainCollection.find_one({"username": username})
        
    except Exception as error:
        return {"error": str(error)}
    
    if not doc:
        return 0 
        
    return int(doc["balance"])


@app.get("/deposit")
async def depositget(amount: float, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    place_id = 87078646939220

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
                result = cursor.fetchone()  
                sitename = result[0]

    except Exception as error:
        return error

    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "amount": amount,
        "deposit" : True
    }

    encoded_data = urllib.parse.quote(json.dumps(launch_data))
    url = f"https://www.roblox.com/games/{place_id}?launchData={encoded_data}"

    return RedirectResponse(url)

@app.get("/withdraw",response_class =  HTMLResponse)
async def withdrawget(amount: float, page: str, request: Request, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    place_id = 87078646939220

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
                result = cursor.fetchone()  
                sitename = result[0]

    except Exception as error:
        return {"error": error}

    mainMongo = getMainMongo()
    mainCollection = mainMongo["collection"]
    
    doc = mainCollection.find_one({"username": sitename})
    print(doc)

    if amount > int(doc["balance"]):
        if page == "towers":
            return templates.TemplateResponse(
                "towers.html",
                {"request": request,"error":"You are trying to withdraw more then you have!"},
                status_code=status.HTTP_400_BAD_REQUEST
            )


    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "amount": amount,
        "deposit" : False
    }

    encoded_data = urllib.parse.quote(json.dumps(launch_data))
    url = f"https://www.roblox.com/games/{place_id}?launchData={encoded_data}"

    return RedirectResponse(url)

@app.post("/depositearnings")
def depositearnings(data: deposit):
    if data.robloxusername == "":
        return "Username can't be empty!"
    if data.siteusername == "":
        return "Site username can't be empty!"
    if data.sessionid == "":
        return "Site sessionid can't be empty!"
    if data.success == None:
        return "Data success can't be empty!"

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE accounts
                    SET robloxusername = %s
                    WHERE username = %s
                    AND  sessionid = %s
                    RETURNING robloxusername;
                """, (data.robloxusername, data.siteusername,data.sessionid))
                row = cur.fetchone()
                conn.commit()

    except Exception as error:
        return error
    
    if row is None:
        return "Something went wrong!"
    else:
        mainMongo = getMainMongo()
        mainCollection = mainMongo["collection"]

        result = mainCollection.update_one(
            {"username": data.siteusername, "sessionid": data.sessionid},
            {"$inc": {"balance": data.amount}},
            upsert=True
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }



@app.post("/withdrawearnings")
def withdrawearnings(data: deposit):
    if data.robloxusername == "":
        return "Username can't be empty!"
    if data.siteusername == "":
        return "Site username can't be empty!"
    if data.sessionid == "":
        return "Site sessionid can't be empty!"
    if data.success == None:
        return "Data success can't be empty!"
    
    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE accounts
                    SET robloxusername = %s
                    WHERE username = %s
                    AND  sessionid = %s
                    RETURNING robloxusername;
                """, (data.robloxusername, data.siteusername,data.sessionid))
                row = cur.fetchone()
                conn.commit()

    except Exception as error:
        return error
    
    if row is None:
        return "Something went wrong!"
    else:
        mainMongo = getMainMongo()
        MainDatabase, mainCollection = mainMongo["db"], mainMongo["collection"]

        result = mainCollection.update_one(
            {"username": data.siteusername, "sessionid": data.sessionid},
            {"$inc": {"balance": data.amount}},
            upsert=True
        )



@app.post("/mines/click")
def print_endpoint(data: MinesClick, SessionId: str = Cookie(None)):
    tile_index = data.tileIndex
    if not tile_index:
        return JSONResponse(content={"error": "No tile index found"}, status_code=400)
    mines = redis.get(SessionId + "minesdata")
    if not mines:
        return JSONResponse(content={"error": "No mines found"}, status_code=400)

    mines = json.loads(mines) 
    is_mine = tile_index in mines

    if is_mine:
        redis.delete("Debounce." + SessionId)
        return JSONResponse(content={"ismine": is_mine,"mines": mines})


    return JSONResponse(content={"ismine": is_mine})

@app.post("/startmines")
def print_endpoint(SessionId: str = Cookie(None)):
    if not SessionId or redis.get("Debounce." + SessionId):
        return RedirectResponse(url="/mines", status_code=303)
    
    redis.set("Debounce." + SessionId,True)

    mines = [i for i in range(48) if random.randint(1,2) == 2]

    redis.set(SessionId + "minesdata",json.dumps(mines))
    return RedirectResponse(url="/mines", status_code=303)


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,  
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Password must be at least 8 characters long"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    session_id = secrets.token_urlsafe(32)

    email = ""  
    robloxusername = ""

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id SERIAL PRIMARY KEY,
                        sessionid TEXT NOT NULL,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        robloxusername VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()

                cur.execute("""
                    INSERT INTO accounts (username, email, password, sessionid,robloxusername)
                    VALUES (%s, %s, %s, %s,%s)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id;
                """, (username, email, hashed_password, session_id,robloxusername))

                row = cur.fetchone()
                if row is None:
                    return templates.TemplateResponse(
                        "register.html",
                        {"request": request, "error": "Username already exists", "username": username},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Database error: {str(e)}", "username": username},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    ten_years_seconds = 10 * 365 * 24 * 60 * 60

    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(
        key="SessionId",
        value=session_id,
        max_age=ten_years_seconds,
        httponly=True,
        path="/"
    )
    return response

@app.post("/login")
def login_post(
    request: Request,  
    username: str = Form(...),
    password: str = Form(...),
):

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:

            with conn.cursor() as cursor:
                cursor.execute("SELECT password, sessionid FROM accounts WHERE username = %s", (username,))

                result = cursor.fetchone()  

                if result and bcrypt.checkpw(password.encode("utf-8"), result[0].encode("utf-8")):

                    ten_years_seconds = 10 * 365 * 24 * 60 * 60

                    response = RedirectResponse(url="/home", status_code=303)
                    response.set_cookie(
                        key="SessionId",
                        value=result[1],
                        max_age=ten_years_seconds,
                        httponly=True,
                        path="/"
                    )
                    return response
                else:
                    raise ValueError("Incorrect Password or username!")
        
    except Exception as error:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"{error}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)

