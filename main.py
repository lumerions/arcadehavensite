from fastapi import FastAPI, Form, Request, Response, Cookie,status,Query
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from upstash_redis import Redis
import psycopg
import bcrypt
import os 
import secrets
import string
import random
from datetime import datetime, timedelta
import webbrowser
from fastapi.staticfiles import StaticFiles
import urllib.parse  
import json
import requests
from pydantic import BaseModel
import time

app = FastAPI(
    title="AH Gambling",
    description="AH Gambling",
    version="1.0.0",
)


class UpdateRobloxUsernameRedis(BaseModel):
    robloxusername: str
    siteusername : str
    sessionid : str



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


@app.get("/balance")
async def get_balance(userId: int = Query(...)):
    database_url = "https://rollsim1-default-rtdb.firebaseio.com"
    accesstoken = "<WzNU3XhKYab3dKNIIMoyOfPpGlBSVgGdeHop38HY>"
    url = f"{database_url}/users/{userId}/balance.json?auth={accesstoken}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching balance:", response.status_code)
        return None

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


@app.get("/robloxdeeplink")
async def get_cookie(SessionId: str | None = Cookie(default=None)):
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
    }

    encoded_data = urllib.parse.quote(json.dumps(launch_data))
    url = f"https://www.roblox.com/games/{place_id}?launchData={encoded_data}"

    return RedirectResponse(url)

@app.post("/setrobloxusername")
def print_endpoint(data: UpdateRobloxUsernameRedis):
    if data.robloxusername == "":
        return "Username can't be empty!"
    if data.siteusername == "":
        return "Site username can't be empty!"
    if data.sessionid == "":
        return "Site sessionid can't be empty!"

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE accounts
                    SET robloxusername = %s
                    WHERE username = %s
                    AND  sessionid = %s;
                """, (data.robloxusername, data.siteusername,data.sessionid))

                conn.commit()
    except Exception as error:
        return error


@app.post("/mines",response_class=HTMLResponse)
def startMines(request: Request):
    cookies = request.cookies
    session_id = cookies.get("SessionId")

    if not session_id:
        return templates.TemplateResponse("mines.html", {"request": request})
    else:
        try:
            with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:

                with conn.cursor() as cursor:
                    cursor.execute("SELECT sessionid,username FROM accounts WHERE sessionid = %s", (session_id,))
                    
                    result = cursor.fetchone()  
                    username = result[1]
                    
                    if result and result[0] != session_id:
                        raise ValueError("Session Id is expired or invalid.")
        
        except Exception as error:
            return templates.TemplateResponse(
                "mines.html",
                {"request": request, "error": f"Error: {error}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    if redis.get(str(session_id)):
        return templates.TemplateResponse("mines.html", {"request": request, "username": username, "session_id": session_id})

    
    redis.set(str(session_id),True)

    return templates.TemplateResponse("mines.html", {"request": request, "username": username, "session_id": session_id})

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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
#cd C:\Users\Admin\Desktop\cra\arcadehavengamble
#python -m uvicorn main:app --reload --host 0.0.0.0 --port 5001
