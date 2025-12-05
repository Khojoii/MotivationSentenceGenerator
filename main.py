# Python standard libraries
import os
import time
# external libraries
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
# Internal project libraries
from model import generate_motivational_sentence
from logger import get_logger

# Load .env variables
load_dotenv()
logger = get_logger()

app = FastAPI()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/inputs")
OUTPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/outputs")

os.makedirs(INPUTS_FOLDER, exist_ok=True)
os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

# Delay control
last_input_time = 0
last_analyze_time = 0
DELAY_SECONDS = 60  # 1 minute

def check_delay(last_time):
    now = time.time()
    elapsed = now - last_time
    if elapsed < DELAY_SECONDS:
        return False, DELAY_SECONDS - int(elapsed)  #remaining time
    return True, now

def get_next_index_file(folder, prefix, ext=".json"):
    """Generate next file name with incremental index"""
    existing = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(ext)]
    indices = []
    for f in existing:
        try:
            index = int(f[len(prefix):-len(ext)])
            indices.append(index)
        except:
            pass
    next_index = max(indices) + 1 if indices else 1
    return os.path.join(folder, f"{prefix}{next_index}{ext}")

@app.post("/input")
async def upload_text(file: UploadFile = File(...)):
    """Upload a .json file and store its content in the inputs folder"""
    global last_input_time
    ok, result = check_delay(last_input_time)
    if not ok:
        seconds_left = result
        logger.error(f"Please wait {seconds_left} seconds before next input upload")
        return JSONResponse(
            content={"error": f"Please wait {seconds_left} seconds before next input upload"},
            status_code=429
        )
    last_input_time = result

    try:
        contents = await file.read()
        text = contents.decode("utf-8").strip()
        if not text:
            logger.warning("Uploaded file is empty")
            return JSONResponse(content={"error": "The uploaded file is empty"}, status_code=400)

        save_path = get_next_index_file(INPUTS_FOLDER, "input")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"Input file uploaded. Saved as {save_path}")
        return {"status": "ok", "filename": file.filename, "saved_path": save_path}

    except Exception as e:
        logger.error(f"Failed to save uploaded file: {repr(e)}")
        return JSONResponse(content={"error": f"Failed to save file: {str(e)}"}, status_code=500)

@app.get("/generate")
async def analyze_text():
    """generate the output based on input"""
    global last_analyze_time
    ok, result = check_delay(last_analyze_time)
    if not ok:
        seconds_left = result
        logger.error(f"Please wait {seconds_left} seconds before next generate")
        return JSONResponse(
            content={"error": f"Please wait {seconds_left} seconds before next generate"},
            status_code=429
        )
    last_analyze_time = result

    try:
        input_files = sorted(os.listdir(INPUTS_FOLDER))
        if not input_files:
            logger.warning("No file uploaded before generate")
            return JSONResponse(content={"error": "No file has been uploaded yet"}, status_code=400)

        input_file_path = os.path.join(INPUTS_FOLDER, input_files[-1])  # latest file
        output_file_path = get_next_index_file(OUTPUTS_FOLDER, "output")

        logger.info(f"generating motivational sentence for {input_file_path}...")
        generate_motivational_sentence(input_file_path, output_file_path)
        logger.info(f"motivational sentence complete, output saved to {output_file_path}")
        return {"status": "ok", "output_file": output_file_path}

    except Exception as e:
        logger.error(f"Error during analysis: {repr(e)}")
        return JSONResponse(content={"error": f"Internal error during generate: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    HOST = os.getenv("HOST") 
    PORT = int(os.getenv("PORT"))  
    logger.info(f"Starting FastAPI app on *.*.*.* : ****")
    uvicorn.run(app, host=HOST, port=PORT)