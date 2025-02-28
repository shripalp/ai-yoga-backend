import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
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

@app.post("/generate_yoga_routine/")
def generate_yoga_routine(user: UserPreferences):
    prompt = f"Generate a {user.fitnessLevel} level yoga routine focused on {user.yogaGoal}. Include warm-up, main poses, and relaxation."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"routine": response.choices[0].message.content}

@app.post("/generate_diet_plan/")
def generate_diet_plan(diet: DietPreferences):
    prompt = f"Generate a one-day meal plan for a person following a {diet.dietType} diet. Include breakfast, lunch, and dinner with healthy ingredients. Also, provide one lifestyle tip."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return {"dietPlan": response.choices[0].message.content}

@app.post("/chatbot")
def chatbot(request: ChatRequest):
    prompt = f"Answer the following yoga or diet-related question: {request.question}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"response": response.choices[0].message.content}