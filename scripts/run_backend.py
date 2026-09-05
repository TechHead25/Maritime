import uvicorn

if __name__ == "__main__":
    print("Starting Maritime Oil-Spill Attribution Backend on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
