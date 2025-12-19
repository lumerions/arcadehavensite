from fastapi import FastAPI,Form,Request
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
