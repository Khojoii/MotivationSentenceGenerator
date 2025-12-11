# Python standard libraries
import os
# External libraries
from fastapi import FastAPI
import uvicorn
# Internal imports
from routes.Endpoints import router
from logger import get_logger

logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="Motivational Sentence Generator API",
    description="API for uploading user data and generating motivational sentences",
)


# Register (include) routers
app.include_router(router, prefix="/motivation", tags=["Motivation"])

logger.info("Application started successfully.")


@app.get("/")
def home():
    logger.info("Root endpoint called.")
    return {"message": "Motivational Sentence Generator API is running"}

if __name__ == "__main__":
    HOST = os.getenv("HOST") 
    PORT = int(os.getenv("PORT"))  
    logger.info(f"Starting FastAPI app on *.*.*.* : ****")
    uvicorn.run(app, host=HOST, port=PORT)