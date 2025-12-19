from fastapi import FastAPI, Form, Request, Response, Cookie,status
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from upstash_redis import Redis
import psycopg
import bcrypt
import os 
import secrets


app = FastAPI(
    title="AH Gambling",
    description="AH Gamblin",
    version="1.0.0",
)

redis = Redis(
    url=os.environ["REDIS_URL"],
    token=os.environ["REDIS_TOKEN"]
)

templates = Jinja2Templates(directory="templates")

@app.get("/register",response_class =  HTMLResponse)
def readregister(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

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
def set_cookie(response: Response):
    ten_years = 10 * 365 * 24 * 60 * 60
    response.set_cookie(
        key="SessionId", 
        value="cookie_value", 
        max_age=ten_years, 
        expires=ten_years,  
        httponly=True
    )
    return {"message": "Cookie has been set to last forever!"}


@app.get("/cookie/get")
def get_cookie(mycookie: str | None = Cookie(default=None)):
    if mycookie:
        return {"SessionId": mycookie}
    return {"message": "No cookie found"}

@app.get("/cookie/delete")
def delete_cookie(response: Response):
    response.delete_cookie(key="SessionId")
    return {"message": "Cookie has been deleted!"}

@app.post("/register", response_class=HTMLResponse)
def register(
    response: Response,  
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
            {"request": request, "error": "Password must be atleast 8 characters long"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
   
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    email = ""  

    try:
        with psycopg.connect(os.environ["POSTGRES_DATABASE_URL"]) as conn:
            with conn.cursor() as cur:

                cur.execute(""" 
                    CREATE TABLE IF NOT EXISTS accounts (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        email VARCHAR(100) NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            
                cur.execute(
                    """
                    INSERT INTO accounts (username, email, password)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username, email) DO NOTHING
                    RETURNING id;
                    """,
                    (username, email, hashed_password)
                )

                row = cur.fetchone()
                if row is None:
                    raise ValueError("Username or email already exists")

    except psycopg.Error as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Database error: {e}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    ten_years = 10 * 365 * 24 * 60 * 60  
    response.set_cookie(
        key="SessionId", 
        value="cookie_value",  
        max_age=ten_years, 
        expires=ten_years,  
        httponly=True  
    )

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    code = secrets.token_urlsafe(32)
    return {"username": username, "password": password,"code": code}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
