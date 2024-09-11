import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Body

app = FastAPI()

@app.post("/add-user")
async def add_user(request: Request, user: dict = Body(...)):
    print(request.headers.items())
    print(user, "added")




if __name__ == "__main__":
    uvicorn.run(app=f"{Path(__file__).stem}:app", host="0.0.0.0", port=8000)