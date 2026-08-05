import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.classification import TicketClassificationList, TicketClassification
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from app.core.config import settings

# Load environment variables
load_dotenv()

# Initialize Langfuse client globally
Langfuse(
    secret_key=settings.LANGFUSE_SECRET_KEY,
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    host=settings.LANGFUSE_BASE_URL
)
langfuse = get_client()

# Verify API key
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the LLM with deterministic temperature=0
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,
    google_api_key=api_key
)

# Configure structured output using the Pydantic list model
structured_llm = llm.with_structured_output(TicketClassificationList)

# Define the system instructions for routing a batch
prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an AI Ticket Router Agent responsible for classifying incoming customer support tickets into the correct department.\n"
        "\n"
        "Here are the specific definitions and rules for the 4 target departments. Classify tickets based on the FEATURE DOMAIN/OWNERSHIP rather than routing every technical bug to Engineering:\n"
        "\n"
        "1. Engineering: bugs, system errors, performance\n"
        "\n"
        "2. Marketing: Handles campaigns, newsletter setups, email template rendering errors, newsletter signup forms, marketing automation rules, A/B testing reports, webinar registration pages, analytics tracking discrepancies, and marketing coupons/campaign codes.\n"
        "\n"
        "3. Support: how-to questions, account issues\n"
        "\n"
        "4. Finance: billing, refunds, subscriptions\n"
        "\n"
        "Routing Instructions:\n"
        "- Read each ticket's title and description carefully.\n"
        "- If a ticket touches more than one department, identify the primary domain/feature category and assign it to the department that owns that business domain.\n"
        "- General rule: whenever a ticket could genuinely and reasonably fit more than one department, output confidence BELOW 0.6, using your own judgment — this applies broadly, not just to the specific patterns below.\n"
        "- Two categories are especially known to be ambiguous in this business, and should ALWAYS get confidence below 0.6 even if you feel fairly sure of the answer:\n"
        "  * (1) any self-service account/billing housekeeping action — plan changes, cancellations, trial extensions, updating billing/account details — that doesn't involve an actual payment failure\n"
        "  * (2) a settings/profile field that fails to save, since this exact failure mode is inconsistently categorized in this business between Engineering and Support.\n"
        "- For tickets that clearly belong to a single department, assign a confidence score ABOVE 0.8.\n"
        "- Provide a short reasoning (1-2 sentences) explaining your decision.\n"
        "- You must return a classification for EVERY ticket in the input list, preserving their IDs correctly."
    )),
    ("user", "Here is the batch of tickets to classify in JSON format:\n{tickets_json}")
])

async def classify_ticket(ticket: dict) -> TicketClassification:
    """Classifies a single support ticket using Gemini 2.5 Flash."""
    # Minimize input token size by only sending id, title, and description
    minimal_ticket = {"id": ticket["id"], "title": ticket["title"], "description": ticket["description"]}
    tickets_json = json.dumps([minimal_ticket], ensure_ascii=False, indent=2)
    prompt = prompt_template.format_messages(tickets_json=tickets_json)
    
    # Initialize the Langfuse CallbackHandler
    langfuse_handler = CallbackHandler()
    
    response = await structured_llm.ainvoke(
        prompt,
        config={
            "callbacks": [langfuse_handler],
            "run_name": "classify_ticket",
            "metadata": {
                "langfuse_tags": ["router", f"ticket_{ticket.get('id', 'unknown')}"]
            }
        }
    )
    return response.classifications[0]
