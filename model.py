#  connect to OpenAI gpt API
# To connect to the OpenAI GPT API, we utilized https://avalai.ir. After signing in, we generated an API key specifically for our project.

# Python standard libraries
import os
import json
# external libraries
from dotenv import load_dotenv
from pydantic import ValidationError
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.callbacks import get_openai_callback
# Internal project libraries
from base_model import force_json_closure,normalize_mixed_text,UserMotivationInput,MotivationOutputValidation
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
    max_tokens=2000, #token limiter
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

def generate_motivational_sentence(input_file: str, output_file: str ):
    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    if "user_info" not in input_data:
        logger.error("JSON does not contain 'user_info' key")
        raise ValueError("Missing 'user_info' key in input JSON")

    try:
        validated_input = UserMotivationInput(**input_data["user_info"])
        logger.info("Input data successfully validated")
    except ValidationError as ve:
        logger.error("Invalid input data!")
        logger.error(ve.json())
        raise

    messages = [
    {
        "role": "system",
        "content": """
You are a maternal/pregnant well-being motivational expert.
Write one heartfelt, personalized motivational sentence based on the user's input.
Output Format (JSON):
{
  "motivational_sentence": "..."
}

Rules:
1. Mention the mother's strengths or positive qualities visible from the data.
2. Mention a **positive near-future event** (ex: meeting her baby, feeling stronger soon, bonding moments with child).
3. Provide gentle, empathetic encouragement, not generic phrases.
4. Include the child’s name if provided.
5. The tone must be warm, human, supportive, not clinical.
6. Never give medical advice.
7. Output must be valid JSON only in the following structure:
"""
    },
    {"role": "user", "content": json.dumps(validated_input.model_dump())}
]
    logger.info("Preparing to send request to OpenAI API")
  
    response = None
    try:
        with get_openai_callback() as cb:
            response = llm.invoke(messages)
            logger.info(cb)

        logger.info("")
        cleaned_text = normalize_mixed_text(response.content.strip())
        cleaned_json = force_json_closure(cleaned_text)
        data = json.loads(cleaned_json)
        result = MotivationOutputValidation(**data)

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