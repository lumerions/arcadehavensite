from fastapi import FastAPI,Form
from fastapi.responses import HTMLResponse,RedirectResponse
from upstash_redis import Redis
import os 

app = FastAPI(
    title="AH Gambling",
    description="AH Gamblin",
    version="1.0.0",
)

redis = Redis(
    url=os.environ["REDIS_URL"],
    token=os.environ["REDIS_TOKEN"]
)


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

@app.get("/test",response_class = HTMLResponse)
def home():
    return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AH Gambling</title>
            <link rel="icon" type="image/x-icon" href="/favicon.ico">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                    background-color: #000000;
                    color: #ffffff;
                    line-height: 1.6;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                }

                header {
                    border-bottom: 1px solid #333333;
                    padding: 0;
                }

                nav {
                    max-width: 1200px;
                    margin: 0 auto;
                    display: flex;
                    align-items: center;
                    padding: 1rem 2rem;
                    gap: 2rem;
                }

                .logo {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: #ffffff;
                    text-decoration: none;
                }

                .nav-links {
                    display: flex;
                    gap: 1.5rem;
                    margin-left: auto;
                }

                .nav-links a {
                    text-decoration: none;
                    color: #888888;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                    font-size: 0.875rem;
                    font-weight: 500;
                }

                .nav-links a:hover {
                    color: #ffffff;
                    background-color: #111111;
                }

                main {
                    flex: 1;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 4rem 2rem;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                }

                .hero {
                    margin-bottom: 3rem;
                }

                .hero-code {
                    margin-top: 2rem;
                    width: 100%;
                    max-width: 900px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                }

                .hero-code pre {
                    background-color: #0a0a0a;
                    border: 1px solid #333333;
                    border-radius: 8px;
                    padding: 1.5rem;
                    text-align: left;
                    grid-column: 1 / -1;
                }

                h1 {
                    font-size: 3rem;
                    font-weight: 700;
                    margin-bottom: 1rem;
                    background: linear-gradient(to right, #ffffff, #888888);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }

                .subtitle {
                    font-size: 1.25rem;
                    color: #888888;
                    margin-bottom: 2rem;
                    max-width: 600px;
                }

                .cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1.5rem;
                    width: 100%;
                    max-width: 900px;
                }

                .card {
                    background-color: #111111;
                    border: 1px solid #333333;
                    border-radius: 8px;
                    padding: 1.5rem;
                    transition: all 0.2s ease;
                    text-align: left;
                }

                .card:hover {
                    border-color: #555555;
                    transform: translateY(-2px);
                }

                .card h3 {
                    font-size: 1.125rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: #ffffff;
                }

                .card p {
                    color: #888888;
                    font-size: 0.875rem;
                    margin-bottom: 1rem;
                }

                .card a {
                    display: inline-flex;
                    align-items: center;
                    color: #ffffff;
                    text-decoration: none;
                    font-size: 0.875rem;
                    font-weight: 500;
                    padding: 0.5rem 1rem;
                    background-color: #222222;
                    border-radius: 6px;
                    border: 1px solid #333333;
                    transition: all 0.2s ease;
                }

                .card a:hover {
                    background-color: #333333;
                    border-color: #555555;
                }

                .status-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    background-color: #0070f3;
                    color: #ffffff;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 500;
                    margin-bottom: 2rem;
                }

                .status-dot {
                    width: 6px;
                    height: 6px;
                    background-color: #00ff88;
                    border-radius: 50%;
                }

                pre {
                    background-color: #0a0a0a;
                    border: 1px solid #333333;
                    border-radius: 6px;
                    padding: 1rem;
                    overflow-x: auto;
                    margin: 0;
                }

                code {
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                    font-size: 0.85rem;
                    line-height: 1.5;
                    color: #ffffff;
                }

                /* Syntax highlighting */
                .keyword {
                    color: #ff79c6;
                }

                .string {
                    color: #f1fa8c;
                }

                .function {
                    color: #50fa7b;
                }

                .class {
                    color: #8be9fd;
                }

                .module {
                    color: #8be9fd;
                }

                .variable {
                    color: #f8f8f2;
                }

                .decorator {
                    color: #ffb86c;
                }

                @media (max-width: 768px) {
                    nav {
                        padding: 1rem;
                        flex-direction: column;
                        gap: 1rem;
                    }

                    .nav-links {
                        margin-left: 0;
                    }

                    main {
                        padding: 2rem 1rem;
                    }

                    h1 {
                        font-size: 2rem;
                    }

                    .hero-code {
                        grid-template-columns: 1fr;
                    }

                    .cards {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <header>
                <nav>
                    <a href="/" class="logo">AH Gambling</a>
                </nav>
            </header>
            <main>
                <div class="cards">
                    <div class="card">
                        <h3>Towers</h3>
                        <p>Towers is a fast-paced risk-and-reward game where every move matters. Climb higher by choosing safe blocks while avoiding hidden traps that can end your run instantly. Each successful step increases your multiplier, but the higher you go, the greater the risk. Cash out at any time to secure your winnings, or push your luck and aim for the top. Simple to play, thrilling to master—Towers rewards sharp instincts and smart timing.</p>
                        <a href="/towers">Open→</a>
                    </div>
                    <div class="card">
                        <h3>Mines</h3>
                        <p>Mines is a high-risk strategy game where danger is hidden beneath every tile. Start the round by choosing how many mines are on the board, then reveal safe spots to build your multiplier. Each safe click boosts your potential payout—but one wrong move ends the game instantly. Cash out whenever you want, or keep going and test your nerve. With full control over risk and reward, Mines is all about precision, patience, and knowing when to stop.</p>
                        <a href="/mines">Open→</a>
                    </div>
                </div>
            </main>
        </body>
        </html>
        """

@app.get("/register",response_class =  HTMLResponse)
def readregister():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register • AH Gambling</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #000000;
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            border-bottom: 1px solid #333333;
        }

        nav {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 2rem;
        }

        .logo {
            color: #ffffff;
            text-decoration: none;
            font-size: 1.25rem;
            font-weight: 600;
        }

        main {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .card {
            background-color: #111111;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 2rem;
            width: 100%;
            max-width: 400px;
        }

        .card h1 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }

        .card p {
            color: #888888;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        label {
            font-size: 0.8rem;
            color: #aaaaaa;
            display: block;
            margin-bottom: 0.25rem;
        }

        input {
            width: 100%;
            padding: 0.6rem 0.75rem;
            margin-bottom: 1rem;
            background-color: #0a0a0a;
            border: 1px solid #333333;
            border-radius: 6px;
            color: #ffffff;
            font-size: 0.9rem;
        }

        input:focus {
            outline: none;
            border-color: #555555;
        }

        button {
            width: 100%;
            padding: 0.6rem;
            background-color: #222222;
            border: 1px solid #333333;
            border-radius: 6px;
            color: #ffffff;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        button:hover {
            background-color: #333333;
            border-color: #555555;
        }

        .footer-text {
            margin-top: 1rem;
            text-align: center;
            font-size: 0.8rem;
            color: #888888;
        }

        .footer-text a {
            color: #ffffff;
            text-decoration: none;
        }

        .footer-text a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
<header>
    <nav>
        <a href="/" class="logo">AH Gambling</a>
    </nav>
</header>

<main>
    <div class="card">
        <h1>Register</h1>
        <p>Create a new account</p>

        <form method="post" action="/register">
            <label>Username</label>
            <input type="text" name="username" required>

            <label>Password</label>
            <input type="password" name="password" required>

            <label>Confirm Password</label>
            <input type="password" name="confirm_password" required>

            <button type="submit">Create Account</button>
        </form>

        <div class="footer-text">
            Already have an account? <a href="/login">Login</a>
        </div>
    </div>
</main>
</body>
</html>
"""


@app.get("/login",response_class =  HTMLResponse)
def readlogin():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login • AH Gambling</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #000000;
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            border-bottom: 1px solid #333333;
        }

        nav {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 2rem;
        }

        .logo {
            color: #ffffff;
            text-decoration: none;
            font-size: 1.25rem;
            font-weight: 600;
        }

        main {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .card {
            background-color: #111111;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 2rem;
            width: 100%;
            max-width: 400px;
        }

        .card h1 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }

        .card p {
            color: #888888;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        label {
            font-size: 0.8rem;
            color: #aaaaaa;
            display: block;
            margin-bottom: 0.25rem;
        }

        input {
            width: 100%;
            padding: 0.6rem 0.75rem;
            margin-bottom: 1rem;
            background-color: #0a0a0a;
            border: 1px solid #333333;
            border-radius: 6px;
            color: #ffffff;
            font-size: 0.9rem;
        }

        input:focus {
            outline: none;
            border-color: #555555;
        }

        button {
            width: 100%;
            padding: 0.6rem;
            background-color: #222222;
            border: 1px solid #333333;
            border-radius: 6px;
            color: #ffffff;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        button:hover {
            background-color: #333333;
            border-color: #555555;
        }

        .footer-text {
            margin-top: 1rem;
            text-align: center;
            font-size: 0.8rem;
            color: #888888;
        }

        .footer-text a {
            color: #ffffff;
            text-decoration: none;
        }

        .footer-text a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
<header>
    <nav>
        <a href="/" class="logo">AH Gambling</a>
    </nav>
</header>

<main>
    <div class="card">
        <h1>Login</h1>
        <p>Access your account</p>

        <form method="post" action="/login">
            <label>Username</label>
            <input type="text" name="username" required>

            <label>Password</label>
            <input type="password" name="password" required>

            <button type="submit">Login</button>
        </form>

        <div class="footer-text">
            Don’t have an account? <a href="/register">Register</a>
        </div>
    </div>
</main>
</body>
</html>
"""

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "password": password}

@app.get("/set")
def set():
    redis.set("foo", "bar")

@app.get("/get")
def set():
    value = redis.get("foo")
    print(value)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return RedirectResponse(url="/register")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
