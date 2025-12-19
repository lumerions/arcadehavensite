from fastapi import FastAPI, Form, Request, Response, Cookie,status
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

from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="AH Gambling",
    description="AH Gambling",
    version="1.0.0",
)

app.mount("/public", StaticFiles(directory="public"), name="public")


redis = Redis(
    url=os.environ["REDIS_URL"],
    token=os.environ["REDIS_TOKEN"]
)

templates = Jinja2Templates(directory="templates")


@app.get("/register", response_class=HTMLResponse)
def readregister(request: Request):
    SessionId = request.cookies.get('SessionId')  
    if not SessionId:
        return templates.TemplateResponse("register.html", {"request": request})
    else:
        try:
            with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:

                with conn.cursor() as cursor:
                    cursor.execute("SELECT sessionid FROM accounts WHERE sessionid = %s", (SessionId,))
                    
                    result = cursor.fetchone()  
                    
                    if result and result[0] == SessionId:
                        return templates.TemplateResponse("home.html", {"request": request})
                    else:
                        response = templates.TemplateResponse("register.html", {"request": request})
                        response.delete_cookie("SessionId")
                        return response
        
        except Exception as error:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": f"Database error: {error}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@app.get("/login",response_class =  HTMLResponse)
def readlogin(request: Request, mycookie: str | None = Cookie(default=None)):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/set")
def set():
    redis.set("foo", "bar")

@app.get("/get")
def get():
    value = redis.get("foo")
    print(value)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return RedirectResponse(url="/register")

@app.get("/test123")
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


@app.get("/cookie/get")
def get_cookie(SessionId: str | None = Cookie(default=None)):
    if SessionId:
        return {"SessionId": SessionId}
    return {"message": "No cookie found"}

@app.get("/cookie/delete")
def delete_cookie(response: Response):
    response.delete_cookie(key="SessionId")
    return {"message": "Cookie has been deleted!"}

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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()

                cur.execute("""
                    INSERT INTO accounts (username, email, password, sessionid)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id;
                """, (username, email, hashed_password, session_id))

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

    response = RedirectResponse(url="/test123", status_code=303)
    response.set_cookie(
        key="SessionId",
        value=session_id,
        max_age=ten_years_seconds,
        httponly=True,
        path="/"
    )
    return response

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    code = secrets.token_urlsafe(32)
    return {"username": username, "password": password,"code": code}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
#cd C:\Users\Admin\Desktop\cra\arcadehavengamble
#python -m uvicorn main:app --reload --host 0.0.0.0 --port 5001
