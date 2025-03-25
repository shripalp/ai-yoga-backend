from fastapi import FastAPI, Request, Header, Response, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os, stripe
from dotenv import load_dotenv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.thirdlimbyoga.com", "https://thirdlimbyoga.com", "http://127.0.0.1:5173" ],  # Allows requests from any frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
client = OpenAI(api_key=OPENAI_API_KEY)


class CheckoutSessionRequest(BaseModel):
    price_id: str


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

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return Response(status_code=400)

    # ✅ Send class link for paid subscriptions
    if event["type"] == "invoice.paid":
        session = event["data"]["object"]
        email = session["customer_email"]

        now = datetime.now()
        expire_date = datetime(now.year, now.month + 1, 1)

        class_link = "https://teams.live.com/meet/9364230714872?p=1MOZamDde4epaQ81Tv"
        send_yoga_email(email, class_link, expire_date)

    # ✅ Send class link for free plans
    elif event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        amount_total = session.get("amount_total", 1)  # in cents

        if amount_total == 0:
            email = session["customer_details"]["email"]
            now = datetime.now()
            expire_date = datetime(now.year, now.month + 1, 1)

            free_link = "https://teams.live.com/meet/9364230714872?p=FreeYogaSession"
            send_yoga_email(email, free_link, expire_date)

    return Response(status_code=200)


def send_yoga_email(to, link, expires_on):
    msg = MIMEText(f"""
    ✅ Welcome to your Monthly Yoga Pass!

    📅 This link is valid until {expires_on.strftime('%B %d, %Y')}:
    👉 {link}

    See you on the mat 🙏
    """)
    msg["Subject"] = "Your Yoga Class Link (Monthly Access)"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)
            print(f"✅ Email sent to {to}")
    except Exception as e:
        print(f"❌ Failed to send email to {to}: {e}")


@app.get("/create-checkout-session")
async def create_checkout_session(
  price_id: str = Query(...),
  mode: str = Query("payment")  # default to one-time payment
  ):
  #BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")

  try:
      session = stripe.checkout.Session.create(
          success_url="https://www.thirdlimbyoga.com/success",
          cancel_url="https://www.thirdlimbyoga.com/cancel",
          payment_method_types=["card"],
          mode=mode,  # 👈 use mode from query param
          line_items=[{
              "price": price_id,
              "quantity": 1,
          }],
      )
      return {"url": session.url}
  except Exception as e:
        print("❌ Stripe error:", e)  # <-- log actual error
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/generate_yoga_routine")
def generate_yoga_routine(yoga_request: UserPreferences):
    formatted_prompt = yoga_prompt.format(
        fitnessLevel=yoga_request.fitnessLevel,
        yogaGoal=yoga_request.yogaGoal
    )

    response = llm.invoke(formatted_prompt)

    return {"routine": response}

@app.post("/generate_diet_plan")
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

