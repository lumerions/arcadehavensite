

from fastapi import FastAPI, Form, Request, Response, Cookie,status,Query
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse,FileResponse
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
from pymongo import MongoClient,UpdateOne
import certifi
import base64
import math
from typing import List, Dict, Any
place_id = 97090711812957

app = FastAPI(
    title="AH Gambling",
    description="AH Gambling",
    version="1.0.0",
)

def getMongoClient(ConnectionURI = None):
    if not ConnectionURI:
        ConnectionURI = os.environ["MONGO_CONNECTIONURI"]
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

def getCoinflipMongo():
    db = Mongo_Client["main"]
    collection = db["coinflips"]
    return {"db": db,"collection":collection}

def getSiteItemsMongo():
    db = Mongo_Client["main"]
    collection = db["siteitems"]
    return {"db": db,"collection":collection}

def redis_int(val, default=0):
    if val is None:
        return default
    if isinstance(val, bytes):
        val = val.decode()
    return int(val)

def MoreWithdraw(pagetype,request):
    if pagetype == "towers":
        return templates.TemplateResponse(
            "towers.html",
            {"request": request,"wallet_error":"You are trying to withdraw more then you have!"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    if pagetype == "mines":
        return templates.TemplateResponse(
            "mines.html",
            {"request": request,"wallet_error":"You are trying to withdraw more then you have!"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
def getMarketplaceData():
    MONGO_URI = os.environ["MONGOINVENTORY_CONNECTIONURI"]
    NewClientInstance = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        tls=True,
        tlsCAFile=certifi.where()
    )

    database = NewClientInstance["cool"]
    collection = database["cp"]
    try:
        MarketplaceData = collection.find(
            {},
        )

        MarketplaceData = list(MarketplaceData)
        return MarketplaceData
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


class deposit(BaseModel):
    robloxusername: str
    siteusername : str
    sessionid : str
    amount : int
    Deposit : bool

class DepositItems(BaseModel):
    robloxusername: str
    userid : int
    siteusername : str
    sessionid : str
    itemdata : List[Dict[str, Any]]
    Deposit : bool

class MinesClick(BaseModel):
    tileIndex: int
    Game : str
class Config:
    extra = "allow"

class Cashout(BaseModel):
    amount: int

redis = Redis(
    url=os.environ["REDIS_URL"],
    token=os.environ["REDIS_TOKEN"]
)


def getPostgresConnection():
    return psycopg.connect(os.environ["POSTGRES_DATABASE_URL"], autocommit=True)

templates = Jinja2Templates(directory="templates")

def CheckIfUserIsLoggedIn(request,htmlfile,htmlfile2,returnusername = None):
    SessionId = request.cookies.get('SessionId')  
    if not SessionId:
        return templates.TemplateResponse(htmlfile, {"request": request})
    else:
        try:
            conn = getPostgresConnection() 
            with conn.cursor() as cursor:
                cursor.execute("SELECT sessionid,robloxusername FROM accounts WHERE sessionid = %s", (SessionId,))
                
                result = cursor.fetchone()  
                
                if result and result[0] == SessionId:
                    if returnusername is None:
                        return templates.TemplateResponse(htmlfile2, {"request": request})
                    else:
                        return result[1]
                else:
                    response = templates.TemplateResponse(htmlfile, {"request": request})
                    response.delete_cookie("SessionId")
                    return response
        
        except Exception as error:
            return templates.TemplateResponse(
                htmlfile,
                {"request": request, "error": f"{error}"},
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
            conn = getPostgresConnection() 
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
                {"request": request, "error": f"{error}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
@app.get("/mines",response_class =  HTMLResponse)
def loadmines(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","mines.html")


@app.get("/towers",response_class =  HTMLResponse)
def towers(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","towers.html")

@app.get("/coinflipgame", response_class=HTMLResponse)
def coinflipHome(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","coinflip.html")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return CheckIfUserIsLoggedIn(request,"register.html","home.html")

@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


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
        doc = mainCollection.find_one({"sessionid": SessionId})
        
    except Exception as error:
        return {"error": str(error)}
    
    if not doc:
        return 0 
        
    return int(doc["balance"])

@app.get("/deposit")
async def depositget(amount: float, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
            result = cursor.fetchone()  

            if result is None:
                return {"error": "Invalid session"}

            sitename = result[0]

    except Exception as error:
        return error

    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "amount": amount,
        "deposit" : True
    }

    json_data = json.dumps(launch_data)
    b64_data = base64.b64encode(json_data.encode()).decode()

    roblox_url = (
        f"https://www.roblox.com/games/start"
        f"?placeId={place_id}"
        f"&launchData={urllib.parse.quote(b64_data)}"
    )

    return RedirectResponse(roblox_url)

@app.get("/withdraw",response_class =  HTMLResponse)
async def withdrawget(amount: float, page: str, request: Request, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
            result = cursor.fetchone()  

            if result is None:
                return {"error": "Invalid session"}

            sitename = result[0]

    except Exception as error:
        return {"error": error}

    mainMongo = getMainMongo()
    mainCollection = mainMongo["collection"]
    
    doc = mainCollection.find_one({"username": sitename})

    def MoreWithdraw(pagetype):
        if pagetype == "towers":
            return templates.TemplateResponse(
                "towers.html",
                {"request": request,"wallet_error":"You are trying to withdraw more then you have!"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if pagetype == "mines":
            return templates.TemplateResponse(
                "mines.html",
                {"request": request,"wallet_error":"You are trying to withdraw more then you have!"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

    if not doc:
        return MoreWithdraw(page)

    if amount > int(doc["balance"]):
        return MoreWithdraw(page)

    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "amount": amount,
        "deposit" : False
    }

    json_data = json.dumps(launch_data)
    b64_data = base64.b64encode(json_data.encode()).decode()

    roblox_url = (
        f"https://www.roblox.com/games/start"
        f"?placeId={place_id}"
        f"&launchData={urllib.parse.quote(b64_data)}"
    )

    return RedirectResponse(roblox_url)


@app.post("/withdrawitems",response_class =  HTMLResponse)
async def withdrawget(request: Request, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    data = await request.json()
    itemdata = data.get("itemdata")

    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
            result = cursor.fetchone()  

            if result is None:
                return {"error": "Invalid session"}

            sitename = result[0]

    except Exception as error:
        return {"error": error}

    SiteItemsCollection = getSiteItemsMongo()["collection"]

    try:
        document = SiteItemsCollection.find_one({"SessionId": SessionId})
        if not document:
            return JSONResponse({"error": "Unknown error"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)
    
    itemsData = document["items"]
    ItemsVerifiedCount = 0

    for item_name, serials in itemdata.items():
        for serial in serials:
            for i,v in enumerate(document["items"]):
                if str(v["itemname"]) == str(item_name) and int(serial.replace("#","")) == int(v["serial"]):
                    ItemsVerifiedCount += 1
                    break


    if ItemsVerifiedCount != len(itemdata):
        return JSONResponse({"error": "Item verification failed!"}, status_code=400)

    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "items": itemdata,
        "itemdeposit" : False
    }

    json_data = json.dumps(launch_data)
    b64_data = base64.b64encode(json_data.encode()).decode()

    roblox_url = (
        f"https://www.roblox.com/games/start"
        f"?placeId={place_id}"
        f"&launchData={urllib.parse.quote(b64_data)}"
    )

    return RedirectResponse(url=roblox_url, status_code=303)

@app.post("/earnings")
def depositearnings(data: deposit):

    if not data.robloxusername:
        return JSONResponse({"error": "Roblox username missing"}, status_code=400)

    if not data.siteusername:
        return JSONResponse({"error": "Site username missing"}, status_code=400)

    if not data.sessionid:
        return JSONResponse({"error": "Session ID missing"}, status_code=400)

    if data.Deposit is None:
        return JSONResponse({"error": "Deposit flag missing"}, status_code=400)

    try:
        amount = abs(int(data.amount))
        if amount <= 0:
            return JSONResponse({"error": "Invalid amount"}, status_code=400)
    except Exception:
        return JSONResponse({"error": "Amount must be an integer"}, status_code=400)

    lock_key = f"earnings:{data.sessionid}"
    if not redis.set(lock_key, "1", nx=True, ex=4):
        return JSONResponse({"error": "Duplicate request detected"}, status_code=429)

    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cur:
            cur.execute(
                "SELECT username FROM accounts WHERE username = %s AND sessionid = %s",
                (data.siteusername, data.sessionid)
            )
            row = cur.fetchone()

            if not row:
                return JSONResponse({"error": "Invalid session"}, status_code=403)

            cur.execute(
                "UPDATE accounts SET robloxusername = %s WHERE username = %s",
                (data.robloxusername, data.siteusername)
            )
            conn.commit()

    except Exception as e:
        return JSONResponse({"error": f"{str(e)}"}, status_code=400)

    mainCollection = getMainMongo()["collection"]

    if data.Deposit:
        result = mainCollection.update_one(
            {"username": data.siteusername, "sessionid": data.sessionid},
            {"$inc": {"balance": amount}},
            upsert=True
        )

        return {"success": True, "type": "deposit", "amount": amount}

    else:
        result = mainCollection.update_one(
            {
                "username": data.siteusername,
                "sessionid": data.sessionid,
                "balance": {"$gte": amount}
            },
            {
                "$inc": {"balance": -amount}
            }
        )

        if result.modified_count == 0:
            return JSONResponse(
                {"error": "Insufficient funds or wallet not found"},
                status_code=400
            )

        return {"success": True, "type": "withdraw", "amount": amount}
    
@app.post("/earningsitems")
def depositearnings(data: DepositItems):

    if not data.robloxusername:
        return JSONResponse({"error": "Roblox username missing"}, status_code=400)

    if not data.siteusername:
        return JSONResponse({"error": "Site username missing"}, status_code=400)

    if not data.sessionid:
        return JSONResponse({"error": "Session ID missing"}, status_code=400)

    if data.Deposit is None:
        return JSONResponse({"error": "Deposit flag missing"}, status_code=400)
    
    if data.userid is None:
        return JSONResponse({"error": "userid missing"}, status_code=400)
    
    if data.itemdata is None or len(data.itemdata) == 0:
        return JSONResponse({"error": "Item data missing"}, status_code=400)

    lock_key = f"earningsitems:{data.sessionid}"
    if not redis.set(lock_key, "1", nx=True, ex=4):
        return JSONResponse({"error": "Duplicate request detected"}, status_code=429)

    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cur:
            cur.execute(
                "SELECT username FROM accounts WHERE username = %s AND sessionid = %s",
                (data.siteusername, data.sessionid)
            )
            row = cur.fetchone()

            if not row:
                return JSONResponse({"error": "Invalid session"}, status_code=403)

            cur.execute(
                "UPDATE accounts SET robloxusername = %s WHERE username = %s",
                (data.robloxusername, data.siteusername)
            )
            conn.commit()

    except Exception as e:
        return JSONResponse({"error": f"{str(e)}"}, status_code=400)

    if data.Deposit:
        getInventoryUrl =  "https://express-js-on-vercel-blue-sigma.vercel.app/GetInventory?id=" + str(data.userid)
        MONGO_URI = os.environ["MONGOINVENTORY_CONNECTIONURI"]
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000,
            tls=True,
            tlsCAFile=certifi.where()
        )

        database = client["cool"]
        collection = database["cp"]

        Response = requests.get(getInventoryUrl)
        decodedResponse = Response.json()
        DataGet = decodedResponse.get("data")
        profile = {
            "Data": {
                "Inventory": {}
            }
        }

        depo = data.itemdata
        ItemsVerified = 0

        for item_id, serials in DataGet.items():
            if item_id not in profile["Data"]["Inventory"]:
                profile["Data"]["Inventory"][item_id] = {}

            for sn in serials:
                profile["Data"]["Inventory"][item_id][sn] = {}

        for i in depo:
            inv = profile["Data"]["Inventory"]
            item_id = str(i["itemid"])

            if item_id in inv:
                inv2 = profile["Data"]["Inventory"][item_id]
                serial = str(i["serial"])
                if serial in inv2:
                    ItemsVerified += 1

        if int(ItemsVerified) != len(data.itemdata):
            return JSONResponse({"error": "Item ownership verification failed!"}, status_code=400)
        
        operations = []

        for item in depo:
            serial = int(item["serial"]) - 1

            newslot = {
                "$set": {
                    f"serials.{serial}.u": "Roblox",
                    f"serials.{serial}.t": int(time.time())
                },
                "$unset": {
                    f"reselling.{serial}.u": ""
                }
            }

            operations.append(
                UpdateOne(
                    {"itemId": int(item["itemid"])},  
                    newslot
                )
            )

        collection.bulk_write(operations)

        SiteItemsCollection = getSiteItemsMongo()["collection"]

        response = SiteItemsCollection.update_one(
            {"SessionId": data.sessionid, "Username": data.siteusername},
            {
                "$push": {
                    "items": {
                        "$each": depo
                    }
                }
            },
            upsert=True
        )

        return {"success": True}
    else:
        SiteItemsCollection = getSiteItemsMongo()["collection"]

        try:
            document = SiteItemsCollection.find_one({"SessionId": data.sessionid})
            if not document:
                return JSONResponse({"error": "document not found"}, status_code=400)

        except Exception as e:
            return JSONResponse({"error": "Unknown error"}, status_code=400)

        found_count = SiteItemsCollection.count_documents({
            "SessionId": str(data.sessionid),
            "Username": str(data.siteusername),
            "items.itemid": {"$in": [i["itemid"] for i in data.itemdata]},
            "items.serial": {"$in": [i["serial"] for i in data.itemdata]}
        })

        if int(found_count) != len(data.itemdata):
            return JSONResponse({"error": "Item verification failed!"}, status_code=400)

        bulk_ops = []

        for item in data.itemdata:
            bulk_ops.append(
                UpdateOne(
                    {"SessionId": str(data.sessionid), "Username": str(data.siteusername)},
                    {"$pull": {"items": {"itemid": int(item["itemid"]), "serial": int(item["serial"])}}}
                )
            )

        if bulk_ops:
            SiteItemsCollection.bulk_write(bulk_ops)
        else:
            return JSONResponse({"error": "No bulk ops"}, status_code=400)

        return {"success": True}


@app.get("/games/getCurrentData")
def get(Game : str,SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "SessionId missing"}, status_code=400)
    keys = [
        "ClickData." + SessionId,
        SessionId + "TowersActive"
    ]

    data_raw, towersactive = redis.mget(*keys)
    data_raw = redis.get("ClickData." + SessionId)

    if towersactive == "1" and Game == "Mines":
        return []

    existing_array = json.loads(data_raw) if data_raw else []
    return existing_array

@app.get("/games/cashoutamount")
def getcashoutAmount(Game: str, Row: int = 0, SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "SessionId missing"}, status_code=400)
    
    if not Game:
        return JSONResponse({"error": "Page missing"}, status_code=400)

    keys = [
        SessionId + "minesdata",
        SessionId + "GameActive",
        SessionId + "Cleared",
        SessionId + "BetAmount",
        SessionId + "Cashout",
        SessionId + "TowersActive"
    ]

    mines_raw, game_active, cleared_raw, bet_amount_raw,CurrentUserAmount,TowerActive = redis.mget(*keys)

    if not mines_raw:
        return JSONResponse({"error": "No mines found"}, status_code=400)

    if not game_active:
        return {"amount": 0, "amountafter": 0, "multiplier": 1}

    try:
        mines = json.loads(mines_raw.decode() if isinstance(mines_raw, bytes) else mines_raw)
        if not isinstance(mines, list):
            mines = []
    except Exception:
        mines = []

    tilescleared = int(cleared_raw) if cleared_raw else 0
    bet_amount = int(bet_amount_raw) if bet_amount_raw else 0

    if Game == "Towers":
        return {
            "amount": CurrentUserAmount,
            "betamount": bet_amount,
            "minescount":len(mines)
        }
    elif Game == "Mines":
        if TowerActive == "1":
            return {
                "amount": 0,
                "amountafter": 0,
                "multiplier": 0
            }
        total_tiles = 25
    else:
        return JSONResponse({"error": "Unknown game"}, status_code=400)

    multiplier_per_click = total_tiles / max(total_tiles - len(mines), 1)
    current_multiplier = multiplier_per_click ** tilescleared
    next_multiplier = multiplier_per_click ** (tilescleared + 1)

    currentamount = int(bet_amount * current_multiplier)
    amountafternexttile = int(bet_amount * next_multiplier)

    return {
        "amount": currentamount,
        "amountafter": amountafternexttile,
        "multiplier": current_multiplier
    }

@app.get("/GetInventory")
def getInventory(SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "SessionId missing"}, status_code=400)
    
    SiteItemsCollection = getSiteItemsMongo()["collection"]

    try:
        document = SiteItemsCollection.find_one({"SessionId": SessionId})
        if not document:
            return JSONResponse({"error": "document not found"}, status_code=400)

    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)
    
    AssetIdParam = ""

    for i,v in enumerate(document["items"]):
        AssetIdParam = AssetIdParam + str(v["itemid"]) + ","

    AssetIdParam = AssetIdParam[:-1]

    MarketplaceData = getMarketplaceData()

    try:
        response = requests.get(f"https://thumbnails.roproxy.com/v1/assets?assetIds={AssetIdParam}&size=512x512&format=Png")
        decodedResponse = response.json()
        decodedResponseData = decodedResponse.get("data")
        for v in document["items"]: 
            for thumb in decodedResponseData:
                if int(thumb["targetId"]) == int(v["itemid"]):
                    v["ImageUrl"] = thumb["imageUrl"]
                    break

            for market in MarketplaceData:
                if int(market["itemId"]) == int(v["itemid"]):  
                    v["Value"] = market["value"]
                    break

        return document["items"]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/deposititems")
async def depositget(request : Request, SessionId: str = Cookie(None)):
    if not SessionId:
        return {"error": "No cookie provided"}
    
    try:
        conn = getPostgresConnection() 

        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM accounts WHERE sessionid = %s", (SessionId,))
            result = cursor.fetchone()  

            if result is None:
                return {"error": "Invalid session"}

            sitename = result[0]

    except Exception as error:
        return error
    
    launch_data = {
        "sitename": str(sitename),
        "sessionid": SessionId,
        "itemdeposit" : True
    }

    json_data = json.dumps(launch_data)
    b64_data = base64.b64encode(json_data.encode()).decode()

    roblox_url = (
        f"https://www.roblox.com/games/start"
        f"?placeId={place_id}"
        f"&launchData={urllib.parse.quote(b64_data)}"
    )

    return RedirectResponse(url=roblox_url, status_code=303)


@app.post("/games/click")
def print_endpoint(data: MinesClick, SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "No session"}, status_code=400)

    tile_index = int(data.tileIndex)
    Game = str(data.Game)
    currentMaxTileIndex = 0

    if Game == "Towers":
        currentMaxTileIndex = 24
    elif Game == "Mines":
        currentMaxTileIndex = 25
    else:
        return JSONResponse({"error": "Unknown game"}, status_code=400)

    cashed_key = SessionId + ":cashed"

    keys = [
        SessionId + "minesdata",
        SessionId + "TowersActive",
        SessionId + "GameActive",
        SessionId + "Row",
        SessionId + ":cashed",
        SessionId + "BetAmount",
        "ClickData." + SessionId,
        SessionId + "Cleared",
        SessionId + "Cashout",
    ]

    mines_raw, towers_active, GameActive, currentRow, cashedAlready, bet_amount, data_raw, tilescleared,CashoutAvailable =  redis.mget(*keys)

    CashoutAvailable = CashoutAvailable or 0

    def decode(value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode()
        return value

    towers_active = decode(towers_active)
    GameActive = decode(GameActive)
    cashedAlready = decode(cashedAlready)
    currentRow = int(currentRow or 0)
    tilescleared = int(tilescleared or 0)
    bet_amount = int(bet_amount or 0)

    if mines_raw is None:
        return JSONResponse({"error": "No mines found"}, status_code=400)

    if towers_active == "1" and Game != "Towers":
        return JSONResponse({"error": "Towers game is currently ongoing!"}, status_code=400)

    if GameActive is None:
        return JSONResponse({"error": "No active game"}, status_code=400)

    if tile_index < 0 or tile_index > currentMaxTileIndex:
        return JSONResponse({"error": "Invalid tile"}, status_code=400)

    if Game == "Towers":
        row = 7 - (tile_index // 3)
        if row > currentRow:
            return JSONResponse(
                {"error": "Row cannot be higher than current row!"},
                status_code=400
            )

    clicks_key = SessionId + ":clicks"
    added =  redis.sadd(clicks_key, tile_index)
    if added == 0:
        return JSONResponse({"error": "Tile already clicked"}, status_code=400)

    if decode(cashedAlready) == "1":
        return JSONResponse({"error": "Game already cashed out"}, status_code=400)

    try:
        if isinstance(mines_raw, bytes):
            mines_raw = mines_raw.decode()
        mines = json.loads(mines_raw)
    except Exception:
        return JSONResponse({"error": "Invalid mines data"}, status_code=400)

    is_mine = tile_index in mines
    if is_mine:
        redis.delete(
            "ClickData." + SessionId,
            SessionId + "Cashout",
            SessionId + "BetAmount",
            SessionId + "Cleared",
            SessionId + ":clicks",
            SessionId + "GameActive",
            SessionId + "TowersActive"
        )
        return JSONResponse({"ismine": True, "mines": mines, "betamount": bet_amount})

    if data_raw:
        if isinstance(data_raw, bytes):
            data_raw = data_raw.decode()
        try:
            existing_array = json.loads(data_raw)
        except Exception:
            existing_array = []
    else:
        existing_array = []

    existing_array.append(tile_index)

    tilescleared += 1

    if Game == "Towers":
        mine_multiplier = ((len(mines) / 23) ** 1.5) + 0.1
        payout = bet_amount * (row + 1) * mine_multiplier * 0.3
        payout = math.floor(payout)
        payoutset = redis_int(CashoutAvailable) + payout
        rowset = currentRow + 1
        redis.mset({
            "ClickData." + SessionId: json.dumps(existing_array),
            SessionId + "Cashout": payoutset,
            SessionId + "Row": rowset
        })
        return JSONResponse({"ismine": False, "betamount": bet_amount, "minescount": len(mines)})
    elif Game == "Mines":
        total_tiles = 25
        multiplier_per_click = total_tiles / (total_tiles - len(mines))
        total_multiplier = multiplier_per_click ** tilescleared
        winnings = int(bet_amount * total_multiplier)
        redis.mset({
            SessionId + "Cashout": winnings,
            "ClickData." + SessionId: json.dumps(existing_array),
            SessionId + "Cleared": tilescleared
        })
        return JSONResponse({"ismine": False})
    else:
        return JSONResponse({"error": "Unknown error"}, status_code=400)



@app.post("/games/start",response_class=HTMLResponse)
async def print_endpoint(request : Request,SessionId: str = Cookie(None)):

    data = await request.json()
    bet_amount = data.get("betAmount")
    mine_count = data.get("mineCount")
    Game = data.get("Game")

    def CheckGame():
        if Game == "Towers":
            return RedirectResponse(url="/towers", status_code=303)
        elif Game == "Mines":
            return RedirectResponse(url="/mines", status_code=303)
        else:
            return templates.TemplateResponse(
                "mines.html",
                {"request": request, "mines_error": "Unknown error"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

    if not SessionId:
        return CheckGame()
            
    if not redis.set("Debounce." + SessionId, 1, nx=True, ex=2):
        return CheckGame()

    def returnTemplate(error):
        return templates.TemplateResponse(
            "mines.html",
            {"request": request, "mines_error": error},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if bet_amount is None or mine_count is None:
        return returnTemplate("Bet amount or mine count is none!")

    if int(mine_count) < 1:
        return returnTemplate("Must be over or equal to 1!")
    
    if int(bet_amount) < 1:
        return returnTemplate("Cannot be a negative number!")

    def IfInsufficientFunds():
        return returnTemplate("Insufficient Funds!")
    
    mainMongo = getMainMongo()
    mainCollection = mainMongo["collection"]

    try:
        conn = getPostgresConnection() 

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
    
    total_tiles = None

    if Game == "Towers":
        total_tiles = 24
    elif Game == "Mines":
        total_tiles = 25
    else:
        return templates.TemplateResponse(
            "mines.html",
            {"request": request, "mines_error": "Unknown error"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    
    if not doc:
        return IfInsufficientFunds()
    if int(doc["balance"]) < int(bet_amount):
        return IfInsufficientFunds()
    if int(mine_count) >= total_tiles:
        return templates.TemplateResponse(
            "mines.html",
            {"request": request, "mines_error": "Mines cant be equal to or over the total tile count!"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    mine_count = min(mine_count, total_tiles)  

    mines = random.sample(range(total_tiles), mine_count)

    result = mainCollection.update_one(
        {"username": username},
        {"$inc": {"balance": -int(bet_amount)}},
        upsert=True
    )

    multiplier_per_click = total_tiles / (total_tiles - mine_count)

    redis.delete(
        SessionId + ":clicks",
        SessionId + ":cashed",
        "ClickData." + SessionId
    )

    if Game == "Towers":
        redis.mset({
            SessionId + "GameActive": "1",
            SessionId + "Cleared": 0,
            SessionId + "Cashout": 0,
            SessionId + "BetAmount": bet_amount,
            SessionId + "minesdata": json.dumps(mines),
            SessionId + "TowersActive": "1",
            SessionId + "Row": 0,
        })
        return RedirectResponse(url="/towers", status_code=303)
    elif Game == "Mines":
        redis.mset({
            SessionId + "GameActive": "1",
            SessionId + "Cleared": 0,
            SessionId + "Cashout": 0,
            SessionId + "BetAmount": bet_amount,
            SessionId + "minesdata": json.dumps(mines),
        })
        return RedirectResponse(url="/mines", status_code=303)
    else:
        return templates.TemplateResponse(
            "mines.html",
            {"request": request, "mines_error": "Unknown error"},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@app.post("/games/cashout")
def cashout(SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "No session"}, status_code=400)
    
    keys = [
        SessionId + "Cashout",
        SessionId + "minesdata",
        SessionId + "BetAmount",
        SessionId + "GameActive"
    ]

    tocashout,mines_raw,betamount,GameActive = redis.mget(*keys)

    if not GameActive:
        return JSONResponse({"error": "No active game"}, status_code=400)
    
    if mines_raw is None:
        return JSONResponse({"error": "No mines found"}, status_code=400)

    cashed_key = SessionId + ":cashed"
    if not redis.set(cashed_key, "1", nx=True,ex = 4):
        return JSONResponse({"error": "Already cashed out"}, status_code=400)

    tocashout = int(tocashout) or 0
    if tocashout <= 0:
        return JSONResponse({"error": "Nothing to cash out"}, status_code=400)

    conn = getPostgresConnection() 

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT username FROM accounts WHERE sessionid = %s",
            (SessionId,)
        )
        row = cursor.fetchone()
        if not row:
            return JSONResponse({"error": "Session not found"}, status_code=400)

        username = row[0]
        mainCollection = getMainMongo()["collection"]
        mainCollection.update_one(
            {"username": username},
            {"$inc": {"balance": tocashout}}
        )


    if isinstance(mines_raw, bytes):
        mines_raw = mines_raw.decode()

    mines = json.loads(mines_raw)

    redis.delete(
        SessionId + "GameActive",
        SessionId + "Cleared",
        SessionId + "Cashout",
        SessionId + "BetAmount",
        "ClickData." + SessionId,
        SessionId + ":clicks",
        SessionId + "TowersActive"
    )

    return JSONResponse({"success": True, "amount": tocashout,"mines": mines,"betamount":betamount})


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
        conn = getPostgresConnection() 
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
            {"request": request, "error": f"{str(e)}", "username": username},
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
        conn = getPostgresConnection() 

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


@app.post("/createcoinflip", response_class=HTMLResponse)
async def CreateCoinflip(request : Request,SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "No session"}, status_code=400)
    was_set = redis.set("CoinflipActive" + SessionId, True, nx=True)
    
    if not was_set:
        return JSONResponse({"error": "Coinflip already active"}, status_code=400)
    
    data = await request.json()
    coinflipData = data.get("coinflipData")
    
    UserCheck = CheckIfUserIsLoggedIn(request,"register.html","coinflip.html")

    try:
        UserCheck = str(UserCheck)
    except Exception as e:
        return UserCheck
    
    SiteItemsCollection = getSiteItemsMongo()["collection"]

    try:
        document = SiteItemsCollection.find_one({"SessionId": SessionId})
        if document is None:
            return JSONResponse({"error": "You do not own any items!"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)
    
    if len(coinflipData) != len(document.items):
        return JSONResponse({"error": "You do not own the items required to create a coinflip!"}, status_code=400)
    
    itemset = set(document["items"])
    coinflipDataSet = set(coinflipData)

    if not coinflipDataSet.issubset(itemset):
        return JSONResponse({"error": "You do not own the items required to create a coinflip!"}, status_code=400)

    CoinflipCollection = getCoinflipMongo()["collection"]

    try:
        document = CoinflipCollection.find_one({"SessionId": SessionId})
        if document:
            return JSONResponse({"error": "Coinflip already exists!"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)

    try:
        SiteItemsCollection.update_one(
            {"SessionId": SessionId, "Username": UserCheck},
            {
                "$pull": {
                    "items": { "$in": coinflipData }
                }
            },
            upsert=True
        )
        CoinflipCollection.update_one(
            {"SessionId": SessionId, "Username": UserCheck},
            {
                "$push": {
                    "CoinflipItems": {
                        "$each": coinflipData
                    }
                }
            },
            upsert=True
        )

        return JSONResponse({"success": True}, status_code=200)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)
    

@app.post("/cancelcoinflip", response_class=HTMLResponse)
async def cancelCoinflip(request : Request,SessionId: str = Cookie(None)):
    if not SessionId:
        return JSONResponse({"error": "No session"}, status_code=400)

    deleted = redis.delete("CoinflipActive" + SessionId)
    if deleted == 0:
        return JSONResponse({"error": "This coinflip already ended or was cancelled already!"}, status_code=400)

    data = await request.json()
    coinflipData = data.get("coinflipData")
    
    UserCheck = CheckIfUserIsLoggedIn(request,"register.html","coinflip.html")
    SiteItemsCollection = getSiteItemsMongo()["collection"]

    try:
        UserCheck = str(UserCheck)
    except Exception as e:
        return UserCheck

    CoinflipCollection = getCoinflipMongo()["collection"]

    try:
        document = CoinflipCollection.find_one({"SessionId": SessionId})
        if document:
            return JSONResponse({"error": "You can only have 1 coinflip active!"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)
    
    coinflipItemsStored = set(document.CoinflipItems)
    coinflipClientItems = set(coinflipData)

    if not coinflipClientItems.issubset(coinflipItemsStored):
        return JSONResponse({"error": "Client side input is not correct!"}, status_code=400)

    try:
        CoinflipCollection.delete_one(
            {"SessionId": SessionId, "Username": UserCheck}
        )

        CoinflipCollection.update_one(
            {"SessionId": SessionId, "Username": UserCheck},
            {
                "$pull": {
                    "CoinflipItems": { "$in": coinflipData }
                }
            },
            upsert=True
        )
        SiteItemsCollection.update_one(
            {"SessionId": SessionId, "Username": UserCheck},
            {
                "$push": {
                    "items": {
                        "$each": coinflipData
                    }
                }
            },
            upsert=True
        )

        return JSONResponse({"success": True}, status_code=200)
    except Exception as e:
        return JSONResponse({"error": "Unknown error"}, status_code=400)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)















