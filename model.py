#  connect to OpenAI gpt API
# To connect to the OpenAI GPT API, we utilized https://avalai.ir. After signing in, we generated an API key specifically for our project.

# Python standard libraries
import os
import json
# external libraries
from dotenv import load_dotenv
from pydantic import ValidationError,BaseModel
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback
# Internal project libraries
from validations.pydantic_validation import (
    UserMotivationInputWrapper,
    DailyMotivationInputWrapper
)
from validations.text_cleaner import normalize_mixed_text , force_json_closure
from logger import get_logger   

logger = get_logger()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger.info("Receiving API key from .env file ...")
if not OPENAI_API_KEY:
    logger.error("API key not found in .env file!")
    raise ValueError("API key not found in .env file!")
else: logger.info("API key received")

llm = ChatOpenAI(
    model="gpt-4o-mini", # in this case we want to use gpt-4o-mini
    base_url="https://api.avalai.ir/v1",
    temperature=0.7,
    max_tokens=1000, #token limiter
    timeout=None,
    max_retries=0,
    api_key=OPENAI_API_KEY)


# testing the API connection and tracking token usage
try:
    logger.info("Testing OpenAI API connection...")
    with get_openai_callback() as cb:
        test_response = llm.invoke([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello world!"}
        ])
        logger.info(cb)
        logger.info("OpenAI API test successful")

except Exception as e:
    logger.error(f"OpenAI API test failed: {repr(e)}")
    raise

#main function for generating 

def base_generate(
    input_file: str,
    output_file: str,
    system_prompt: str,
    output_validation_model: type[BaseModel],
    daily:bool):# Determine whether the entry is daily or not

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = json.load(f)
        logger.info("Input file loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to read input file: {repr(e)}")
        raise
    #chosing the right wrapper
    wrapper_class = DailyMotivationInputWrapper if daily else UserMotivationInputWrapper

    if "user_info" not in input_data:
        logger.error("JSON does not contain 'user_info' key")
        raise ValueError("Missing 'user_info' key in input JSON")

    try:
        input_wrapper = wrapper_class(**input_data)
        logger.info(f"Input JSON validated successfully using {wrapper_class.__name__}")
    except ValidationError as ve:
        logger.error(f"Input JSON validation failed: {ve.json()}")
        raise

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_wrapper.model_dump(), ensure_ascii=False)}
    ]
    logger.info("Preparing to send request to OpenAI API")
  
    response = None
    try:
        with get_openai_callback() as cb:
            response = llm.invoke(messages)
            logger.info(cb)
        cleaned_text = normalize_mixed_text(response.content.strip())
        cleaned_json = force_json_closure(cleaned_text)
        data = json.loads(cleaned_json)
        result = output_validation_model(**data)

        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(result.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)


    except ValidationError as ve:
        logger.error("Model output does not match expected structure!")
        logger.error(ve.json())
        logger.error(f"Raw model output: {response.content if response else 'No response'}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {repr(e)}")
        logger.error(f"Raw model output: {response.content if response else 'No response'}")
        raise
