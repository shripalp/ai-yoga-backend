from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserPreferences(BaseModel):
    fitnessLevel: str
    yogaGoal: str

class DietPreferences(BaseModel):
    dietType: str

class ChatRequest(BaseModel):
    question: str

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)

# Template for Yoga Routine
yoga_prompt = PromptTemplate(
    input_variables=["fitnessLevel", "yogaGoal"],
    template="""
    Generate a structured yoga routine for a {fitnessLevel} level person focusing on {yogaGoal}. 
    Format the response as follows:
    
    **Yoga Routine for {yogaGoal}**
    - **Warm-up (5 minutes):**
      - [List warm-up poses]
    - **Main Yoga Poses (20 minutes):**
      - [List yoga poses with duration]
    - **Cool-down (5 minutes):**
      - [List cool-down poses]

    Ensure it's clear and concise.
    """
)
# Template for Diet Plan
diet_prompt = PromptTemplate(
    input_variables=["dietType"],
    template="""
    Generate a structured daily meal plan for a person following a {dietType} diet.
    Format the response as follows:

    **Daily Meal Plan ({dietType})**
    - **Breakfast:**
      - [List breakfast meal]
    - **Lunch:**
      - [List lunch meal]
    - **Dinner:**
      - [List dinner meal]
    - **Lifestyle Tip:**
      - [Provide one healthy lifestyle tip]

    Ensure it's easy to read.
    """
)

@app.post("/generate-yoga-routine")
def generate_yoga_routine(yoga_request: UserPreferences):
    formatted_prompt = yoga_prompt.format(
        fitnessLevel=yoga_request.fitnessLevel,
        yogaGoal=yoga_request.yogaGoal
    )

    response = llm.invoke(formatted_prompt)

    return {"routine": response}

@app.post("/generate-diet-plan")
def generate_diet_plan(diet_request: DietPreferences):
    formatted_prompt = diet_prompt.format(dietType=diet_request.dietType)

    response = llm.invoke(formatted_prompt)

    return {"dietPlan": response}

@app.post("/chatbot")
def chatbot(request: ChatRequest):
    prompt = f"Answer the following yoga or diet-related question: {request.question}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"response": response.choices[0].message.content}