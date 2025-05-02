from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define the LangGraph state schema
class ItineraryState(TypedDict):
    city: str
    interests: str
    days: int
    itinerary: str
    destination_suggestions: str
    budget: str
    season: str

# Configuration - use environment variables in production
GROQ_API_KEY = "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"
MODEL_NAME = "llama3-70b-8192"

# Initialize LLM
llm = ChatGroq(
    temperature=0.5,
    groq_api_key=GROQ_API_KEY,
    model_name=MODEL_NAME,
    timeout=30
)

# Prompt template for itinerary generation
prompt_template = ChatPromptTemplate.from_template("""
You are a professional travel planner creating a {days}-day itinerary for {city} focused on: {interests}.

STRICT FORMAT:
### Day [X]
- Morning: [Activity] - [1 sentence]
- Lunch: [Restaurant] - [Cuisine]
- Afternoon: [Activity] - [1 sentence]
- Dinner: [Restaurant] - [Cuisine]
- Evening: [Activity] - [1 sentence]

MUST FOLLOW:
- Use hyphens for bullets
- One activity per line
- No double punctuation
- Do not include disclaimers or comments
""")

# Prompt for destination suggestions
destination_prompt_template = ChatPromptTemplate.from_template("""
Given the following travel preferences, suggest three beach destinations in India:

Interests: {interests}
Budget: {budget}
Season: {season}

Each suggestion should include the name and a 1-2 sentence description.
""")

# Node: Generate itinerary
def generate_itinerary_node(state: ItineraryState) -> ItineraryState:
    prompt = prompt_template.format(
        city=state["city"],
        interests=state["interests"],
        days=max(1, min(state["days"], 14))
    )
    response = llm.invoke(prompt)

    clean_lines = []
    for line in response.content.split('\n'):
        line = line.replace('•', '-').replace('*', '-')
        line = line.replace(' -', '-').replace('- ', '- ')
        if line.strip():
            clean_lines.append(line.strip())

    return {
        **state,
        "itinerary": '\n'.join(clean_lines)
    }

# Node: Suggest destinations
def suggest_destinations_node(state: ItineraryState) -> ItineraryState:
    prompt = destination_prompt_template.format(
        interests=state["interests"],
        budget=state.get("budget", "moderate"),
        season=state.get("season", "any")
    )
    response = llm.invoke(prompt)

    return {
        **state,
        "destination_suggestions": response.content.strip()
    }

# Build LangGraph
builder = StateGraph(ItineraryState)
builder.add_node("generate_itinerary", generate_itinerary_node)
builder.add_node("suggest_destinations", suggest_destinations_node)
builder.set_entry_point("generate_itinerary")
builder.add_edge("generate_itinerary", "suggest_destinations")
builder.add_edge("suggest_destinations", END)
graph = builder.compile()

# Test runner
if __name__ == "__main__":
    input_data = {
        "city": "Tokyo",
        "interests": "culture, food, anime",
        "days": 3,
        "budget": "moderate",
        "season": "spring"
    }
    result = graph.invoke(input_data)
    print("Itinerary:\n", result["itinerary"])
    print("\nSuggested Destinations:\n", result["destination_suggestions"])
