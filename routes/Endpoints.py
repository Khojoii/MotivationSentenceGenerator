# Python standard libraries
import os
import json
# external libraries
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
# internal imports
from validations.pydantic_validation import (MotivationOutputValidation,UserMotivationInputWrapper,DailyMotivationInputWrapper)

from model import base_generate
from logger import get_logger
from delay_control import check_delay
from file_indexer import get_next_index_file
import prompts
logger = get_logger()

router = APIRouter()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(BASE_PATH)  # back to root

INPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/inputs")
OUTPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/outputs")
DAILY_INPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/daily_inputs" )
DAILY_OUTPUTS_FOLDER = os.path.join(BASE_PATH, "Inputs_Outputs/daily_outputs" )

os.makedirs(INPUTS_FOLDER, exist_ok=True)
os.makedirs(OUTPUTS_FOLDER, exist_ok=True)
os.makedirs(DAILY_INPUTS_FOLDER, exist_ok=True)
os.makedirs(DAILY_OUTPUTS_FOLDER,exist_ok=True)

# Delay control
last_input_time = 0
last_analyze_time = 0
last_daily_input_time = 0
last_daily_analyze_time = 0

@router.post("/input")
async def upload_input_json(file: UploadFile = File(...)):
    logger.info("Received request: POST /input")

    global last_input_time
    ok, result = check_delay(last_input_time)

    if not ok:
        wait_seconds = result
        logger.warning(f"Rate limit: must wait {wait_seconds} seconds before next /input request.")
        return JSONResponse(
            content={"error": f"Please wait {wait_seconds} seconds before next input upload"},
            status_code=429
        )

    last_input_time = result
    logger.info("Rate-limit check passed for /input")

    try:
        # 1. Read file
        contents = await file.read()
        text = contents.decode("utf-8").strip()

        if not text:
            logger.warning("Upload failed: empty file content.")
            return JSONResponse(content={"error": "The uploaded file is empty"}, status_code=400)

        logger.info(f"File content read successfully. Filename={file.filename}")

        # 2. JSON validation using Pydantic
        try:
            parsed_json = UserMotivationInputWrapper(**json.loads(text))
            logger.info("JSON validation passed (UserMotivationInput).")
        except Exception as e:
            logger.error(f"JSON validation failed: {repr(e)}")
            return JSONResponse(
                content={"error": "Invalid JSON format or missing required fields", "details": str(e)},
                status_code=400
            )
        # 3. Save validated JSON file
        save_path = get_next_index_file(INPUTS_FOLDER, "input")

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(
            f"Input JSON saved successfully. Original={file.filename} | Saved={save_path}"
        )

        return {
            "status": "ok",
            "filename": file.filename,
            "saved_path": save_path,
            "validated_data": parsed_json.model_dump()
        }

    except Exception as e:
        logger.error(f"Unexpected exception in /input: {repr(e)}")
        return JSONResponse(content={"error": "Internal server error", "details": str(e)}, status_code=500)

    
@router.post("/input_daily")
async def upload_daily_input_json(file: UploadFile = File(...)):
    logger.info("Received request: POST /input_daily")

    global last_daily_input_time
    ok, result = check_delay(last_daily_input_time)

    if not ok:
        wait_seconds = result
        logger.warning(f"Rate limit: must wait {wait_seconds} seconds before next /input_daily request.")
        return JSONResponse(
            content={"error": f"Please wait {wait_seconds} seconds before next daily input upload"},
            status_code=429
        )

    last_daily_input_time = result
    logger.info("Rate-limit check passed for /input_daily")

    try:
        # 1. Read uploaded file
        contents = await file.read()
        text = contents.decode("utf-8").strip()

        if not text:
            logger.warning("Daily upload failed: empty file content.")
            return JSONResponse(content={"error": "The uploaded file is empty"}, status_code=400)

        logger.info(f"Daily file content read successfully. Filename={file.filename}")

        # 2. JSON validation using Pydantic
        try:
            parsed_json = DailyMotivationInputWrapper(**json.loads(text))
            logger.info("JSON validation passed (DailyMotivationInput).")
        except Exception as e:
            logger.error(f"Daily JSON validation failed: {repr(e)}")
            return JSONResponse(
                content={"error": "Invalid JSON format or missing required fields", "details": str(e)},
                status_code=400
            )

        # 3. Save validated JSON file
        save_path = get_next_index_file(DAILY_INPUTS_FOLDER, "input")

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(
            f"Daily input JSON saved successfully. Original={file.filename} | Saved={save_path}"
        )

        return {
            "status": "ok",
            "filename": file.filename,
            "saved_path": save_path,
            "validated_data": parsed_json.model_dump()
        }

    except Exception as e:
        logger.error(f"Unexpected exception in /input_daily: {repr(e)}")
        return JSONResponse(
            content={"error": "Internal server error", "details": str(e)},
            status_code=500
        )


@router.get("/generate")
async def generate_json():
    logger.info("Received request: /generate (generate_json)")

    global last_analyze_time

    ok, result = check_delay(last_analyze_time)
    if not ok:
        logger.warning(f"Generate request rejected due to delay. Must wait {result} seconds.")
        return JSONResponse(
            content={"error": f"Please wait {result} seconds before next generate"},
            status_code=429
        )

    last_analyze_time = result
    logger.info("Rate-limit check passed for /generate")

    try:
        input_files = sorted(os.listdir(INPUTS_FOLDER))
        if not input_files:
            logger.warning("Generate failed: no input files found.")
            return JSONResponse(content={"error": "No file has been uploaded yet"}, status_code=400)

        input_file_path = os.path.join(INPUTS_FOLDER, input_files[-1])
        logger.info(f"Selected latest input file: {input_file_path}")

        output_file_path = get_next_index_file(OUTPUTS_FOLDER, "output")
        logger.info(f"Generating output file: {output_file_path}")

        base_generate(input_file_path, output_file_path,prompts.SINGLE_GENERATE_PROMPT,MotivationOutputValidation,False)

        logger.info(f"Generation completed. Output saved to {output_file_path}")
        return {"status": "ok", "output_file": output_file_path}

    except Exception as e:
        logger.error(f"Exception in /generate: {repr(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@router.get("/generate_daily")
async def generate_daily_json():
    logger.info("Received request: /generate_daily (generate_json)")

    global last_daily_analyze_time

    ok, result = check_delay(last_daily_analyze_time)
    if not ok:
        logger.warning(f"Generate request rejected due to delay. Must wait {result} seconds.")
        return JSONResponse(
            content={"error": f"Please wait {result} seconds before next generate"},
            status_code=429
        )

    last_daily_analyze_time = result
    logger.info("Rate-limit check passed for /generate_daily")

    try:
        input_files = sorted(os.listdir(DAILY_INPUTS_FOLDER))
        if not input_files:
            logger.warning("Generate failed: no input files found.")
            return JSONResponse(content={"error": "No file has been uploaded yet"}, status_code=400)

        input_file_path = os.path.join(DAILY_INPUTS_FOLDER, input_files[-1])
        logger.info(f"Selected latest input file: {input_file_path}")

        output_file_path = get_next_index_file(DAILY_OUTPUTS_FOLDER, "output")
        logger.info(f"Generating output file: {output_file_path}")

        base_generate(input_file_path, output_file_path,prompts.DAILY_GENERATE_PROMPT,MotivationOutputValidation,True)

        logger.info(f"Generation completed. Output saved to {output_file_path}")
        return {"status": "ok", "output_file": output_file_path}

    except Exception as e:
        logger.error(f"Exception in /generate_daily: {repr(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
