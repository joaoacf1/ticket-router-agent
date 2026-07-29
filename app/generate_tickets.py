import os
import json
import time
import random
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Define the output structure for a batch of tickets
class Ticket(BaseModel):
    id: int = Field(description="Unique incremental ID of the ticket")
    title: str = Field(description="The title of the support ticket")
    description: str = Field(description="The detailed description of the ticket in English, containing 2 to 4 sentences, in a realistic customer tone (not too formal, using everyday slangs or frustrations if appropriate)")
    actual_department: str = Field(description="The actual department: Engineering, Marketing, Support, or Finance")
    is_ambiguous: bool = Field(description="Boolean indicating if the ticket is ambiguous (could fit into 2 departments)")

class TicketList(BaseModel):
    tickets: list[Ticket]

def generate_tickets():
    # Verify API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found in .env")
        return

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=api_key
    )
    
    # Configure structured output
    structured_llm = llm.with_structured_output(TicketList)

    departments = ["Engineering", "Marketing", "Support", "Finance"]
    
    # We want exactly 200 tickets: 50 per department.
    # 15% of 200 = 30 ambiguous tickets in total.
    # Let's distribute ambiguous tickets:
    # Engineering: 8 ambiguous, 42 normal
    # Marketing: 7 ambiguous, 43 normal
    # Support: 8 ambiguous, 42 normal
    # Finance: 7 ambiguous, 43 normal
    # Total: 30 ambiguous, 170 normal.
    
    # Prompt template for batch generation
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert synthetic data generator specialized in creating realistic support tickets for a tech/SaaS company.\n"
            "Generate exactly 100 support tickets in English distributed according to the instructions below.\n"
            "\n"
            "Department distribution for these 100 tickets:\n"
            "- Engineering: {eng_normal} normal and {eng_ambig} ambiguous.\n"
            "- Marketing: {mkt_normal} normal and {mkt_ambig} ambiguous.\n"
            "- Support: {sup_normal} normal and {sup_ambig} ambiguous.\n"
            "- Finance: {fin_normal} normal and {fin_ambig} ambiguous.\n"
            "\n"
            "Field Instructions:\n"
            "- id: incremental starting at {start_id}.\n"
            "- title: Concise, describing the problem/query.\n"
            "- description: 2 to 4 sentences. The tone must be of a real customer (non-technical/layperson), expressing daily frustrations, perhaps minor grammatical slips or informal tone, not overly polished or polite.\n"
            "- actual_department: Must be exactly the primary department (Engineering, Marketing, Support, or Finance).\n"
            "- is_ambiguous: Boolean (true/false).\n"
            "\n"
            "Ambiguity Definition:\n"
            "- If is_ambiguous is true, the description should border between two departments (e.g. Engineering and Finance, Marketing and Support, etc.), where the user mentions something from both contexts realistically.\n"
            "Example of ambiguous ticket for Engineering: 'The system failed when processing my payment, but the screen froze. Finance said they didn't receive it. Can you check if it's a code bug?' (Engineering + Finance).\n"
            "Example of ambiguous ticket for Marketing: 'I want to redeem the coupon campaign code I got in my email, but the button is greyed out and I can't click it.' (Marketing + Engineering/Support).\n"
            "- If is_ambiguous is false, the description should clearly point to the designated department only."
        )),
        ("user", "Generate the 100 tickets now, starting the IDs at {start_id}.")
    ])

    print("Starting generation of 200 support tickets...")
    
    # Define batch configurations
    batches_config = [
        # Batch 1 (100 tickets)
        {
            "start_id": 1,
            "eng_normal": 21, "eng_ambig": 4,
            "mkt_normal": 21, "mkt_ambig": 4,
            "sup_normal": 21, "sup_ambig": 4,
            "fin_normal": 22, "fin_ambig": 3
        },
        # Batch 2 (100 tickets)
        {
            "start_id": 101,
            "eng_normal": 21, "eng_ambig": 4,
            "mkt_normal": 22, "mkt_ambig": 3,
            "sup_normal": 21, "sup_ambig": 4,
            "fin_normal": 21, "fin_ambig": 4
        }
    ]

    all_tickets = []
    
    for idx, config in enumerate(batches_config):
        print(f"\nGenerating Batch {idx + 1}/2 ({config['start_id']} to {config['start_id'] + 99})...")
        
        prompt = prompt_template.format_messages(
            start_id=config["start_id"],
            eng_normal=config["eng_normal"], eng_ambig=config["eng_ambig"],
            mkt_normal=config["mkt_normal"], mkt_ambig=config["mkt_ambig"],
            sup_normal=config["sup_normal"], sup_ambig=config["sup_ambig"],
            fin_normal=config["fin_normal"], fin_ambig=config["fin_ambig"]
        )
        
        success = False
        for attempt in range(4):
            try:
                response = structured_llm.invoke(prompt)
                batch_tickets = response.tickets
                
                if len(batch_tickets) > 0:
                    all_tickets.extend(batch_tickets)
                    print(f"Success: {len(batch_tickets)} tickets added in Batch {idx + 1}.")
                    success = True
                    break
                else:
                    print("Response returned empty ticket list. Retrying...")
            except Exception as e:
                print(f"Error in Batch {idx + 1} (Attempt {attempt + 1}/4): {e}")
                print("Waiting 30 seconds before retrying...")
                time.sleep(30)
                
        if not success:
            print(f"Critical Error: Could not get response for Batch {idx + 1}.")
            return
            
        if idx < len(batches_config) - 1:
            print("Waiting 10 seconds cooldown between batches...")
            time.sleep(10)

    # Final validation and adjustments
    print("\nProcessing and validating generated tickets...")
    
    # Shuffle lists to mix departments and ambiguities
    random.shuffle(all_tickets)
    
    # Re-assign IDs after shuffle so they are in sequential order 1..200
    for idx, ticket in enumerate(all_tickets):
        ticket.id = idx + 1

    # Convert to dict for saving
    tickets_dict = [t.model_dump() for t in all_tickets]
    
    # Save path
    os.makedirs("data", exist_ok=True)
    output_path = "data/tickets.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tickets_dict, f, ensure_ascii=False, indent=2)
        
    print(f"\nGeneration completed! Total tickets saved: {len(tickets_dict)}")
    print(f"Saved in: {output_path}")
    
    # Validation stats
    dept_counts = {}
    ambig_count = 0
    for t in tickets_dict:
        dept = t["actual_department"]
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        if t["is_ambiguous"]:
            ambig_count += 1
            
    print("\nValidation Stats:")
    for d, c in dept_counts.items():
        print(f"- {d}: {c} tickets")
    print(f"- Ambiguous Tickets: {ambig_count} ({ambig_count / len(tickets_dict) * 100:.1f}%)")

if __name__ == "__main__":
    generate_tickets()
