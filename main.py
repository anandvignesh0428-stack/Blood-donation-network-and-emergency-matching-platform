from fastapi import FastAPI

app = FastAPI(title="Blood Donation Network")

@app.get("/")
def home():
    return {
        "message": "Blood Donation Network API is running!"
    }