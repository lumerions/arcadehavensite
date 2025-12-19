from fastapi import FastAPI, Form, Request, Response, Cookie
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from upstash_redis import Redis
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

@app.get("/api/data")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300}
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {
            "id": item_id,
            "name": "Sample Item " + str(item_id),
            "value": item_id * 100
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/register",response_class =  HTMLResponse)
def readregister(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login",response_class =  HTMLResponse)
def readlogin(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    code = secrets.token_urlsafe(32)
    return {"username": username, "password": password,"code": code}

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
        key="mycookie", 
        value="cookie_value", 
        max_age=ten_years, 
        expires=ten_years,  # ensures browser keeps it for a long time
        httponly=True
    )
    return {"message": "Cookie has been set to last forever!"}


@app.get("/cookie/get")
def get_cookie(mycookie: str | None = Cookie(default=None)):
    if mycookie:
        return {"mycookie": mycookie}
    return {"message": "No cookie found"}


@app.get("/cookie/delete")
def delete_cookie(response: Response):
    response.delete_cookie(key="mycookie")
    return {"message": "Cookie has been deleted!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
