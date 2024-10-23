from fastapi import FastAPI
from routers import story_router
import uvicorn

app = FastAPI(title="Crime Story Game API")
app.include_router(story_router.router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
