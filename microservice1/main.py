import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/add-user")
async def add_user(request: Request, user: dict):
    print(request.headers)
    print(user, "added")




if __name__ == "__main__":
    uvicorn.run("0.0.0.0", port=8080)