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

class TherapyRequest(BaseModel):
    problem_statement: str  # Accepts user's problem statement

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

# Template for Yoga Therapy Plan
therapy_prompt = PromptTemplate(
    input_variables=["problem_statement"],
    template="""
    Generate a personalized Yoga Therapy Plan for the following problem:

    **Problem:** {problem_statement}

    The response should include:
    1. **Understanding the Problem**: Explain how yoga can help.
    2. **Recommended Yoga Poses**: List specific poses with benefits.
    3. **Breathing Techniques**: Explain breathwork techniques for healing.
    4. **Relaxation Practices**: Include meditation or mindfulness practices.
    5. **Lifestyle Suggestions**: Provide additional wellness tips.

    Ensure the response is structured, easy to follow, and holistic.
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

@app.post("/generate_yoga_therapy_plan")
def generate_yoga_therapy_plan(request: TherapyRequest):
    system_prompt = """
    You are an expert Yoga Therapist with deep knowledge of holistic healing, yoga postures, breathing techniques, 
    and wellness. Your goal is to provide structured, personalized yoga therapy plans that are in line with Iyengar Yoga Tradition and are **clear, effective, and easy to follow**.
    
    Guidelines:
    - Use **simple, understandable language** (avoid medical jargon).
    - Structure the plan clearly with **step-by-step instructions**.
    - Always include **Yoga Poses, Breathwork Techniques, Relaxation Practices, and Lifestyle Suggestions**.
    - Make the response **motivating and encouraging**.
    """

    user_prompt = f"""
    Generate a **personalized Yoga Therapy Plan** for the following problem:

    **Problem:** {request.problem_statement}

    The response should include:
    1. **Understanding the Problem**: Explain how yoga can help.
    2. **Recommended Yoga Poses**: List specific poses with benefits.
    3. **Breathing Techniques**: Explain breathwork techniques for healing.
    4. **Relaxation Practices**: Include meditation or mindfulness practices.
    5. **Lifestyle Suggestions**: Provide additional wellness tips.

    **Format the response in a structured, easy-to-follow way.**
    """

    # Combine system and user prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    response = llm.invoke(full_prompt)
    
    return {"therapyPlan": response}

