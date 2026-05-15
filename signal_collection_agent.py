import os
import json
from typing import Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. JSON Schema Definition (Pydantic)
# ------------------------------------------------------------------
class SignalOutput(BaseModel):
    normalized_text: str = Field(
        description="The cleaned, translated (to English), and normalized version of the input text."
    )
    location: Optional[str] = Field(
        description="The specific geographic location mentioned (e.g., 'G-10', 'Lahore', 'Mall Road'). Null if none found."
    )
    urgency_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        description="The assessed urgency of the situation based on the text."
    )
    source_classification: Literal["Social Media", "Emergency Complaint", "Weather Alert", "Traffic Update", "Unknown"] = Field(
        description="The predicted source or category of this signal."
    )
    confidence_score: float = Field(
        description="A score from 0.0 to 1.0 representing how confident the AI is in this extraction."
    )
    language_detected: str = Field(
        description="The original language of the input (e.g., 'English', 'Roman Urdu')."
    )

# ------------------------------------------------------------------
# 2. Prompt Engineering Strategy
# ------------------------------------------------------------------
# We use a zero-shot, role-based prompt with explicit constraints for 
# handling multilingual input (like Roman Urdu) and strict JSON formatting.

PROMPT_TEMPLATE = """
You are the Signal Collection Agent for CIRO (Crisis Intelligence & Response Orchestrator).
Your job is to analyze incoming unstructured crisis signals (which may be in English, Urdu, Roman Urdu, or mixed) and extract structured intelligence.

Input Signal: "{raw_signal}"

Tasks:
1. Normalize and translate the text to clear English.
2. Extract any specific geographic location mentioned.
3. Assess the urgency (Low, Medium, High, Critical). Context: "pani bhar gaya hai" (flooding) or "jammed" signifies High/Critical urgency.
4. Classify the likely source of the signal (Social Media, Emergency Complaint, Weather Alert, Traffic Update).
5. Assign a confidence score (0.0 to 1.0) based on how clear, specific, and actionable the signal is.

{format_instructions}

Analyze the input strictly and provide the JSON output exactly as requested.
"""

# ------------------------------------------------------------------
# 3. Agent Implementation & Workflow Logic
# ------------------------------------------------------------------
class SignalCollectionAgent:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Initialize the LLM with 0 temperature for deterministic JSON output
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0, 
            max_retries=3 # Error Handling: Built-in retries for API failures
        )
        # Binds the Pydantic schema to the Langchain parser
        self.parser = PydanticOutputParser(pydantic_object=SignalOutput)
        
        self.prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["raw_signal"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # LCEL (LangChain Expression Language) Pipeline
        self.chain = self.prompt | self.llm | self.parser

    def process_signal(self, raw_signal: str) -> Optional[SignalOutput]:
        """
        Main workflow logic: Ingest -> Parse -> Validate -> Return
        """
        try:
            # 1. Execute the LangChain pipeline
            result = self.chain.invoke({"raw_signal": raw_signal})
            
            # 2. Confidence Scoring Logic & Alerting
            if result.confidence_score < 0.5:
                print(f"[Warning] Low confidence score ({result.confidence_score}) for signal: {raw_signal}")
                # Future: Route to a "Human Review" queue instead of auto-processing
                
            # 3. Return the fully structured Pydantic object
            return result

        except ValidationError as ve:
            # Error Handling: If the LLM hallucinates keys, Pydantic catches it
            print(f"[Error] JSON Schema Validation Failed: {ve}")
            return None
        except Exception as e:
            # Error Handling: API outages, rate limits, etc.
            print(f"[Error] Failed to process signal via LLM: {e}")
            return None

# ------------------------------------------------------------------
# 4. Execution & Testing
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Note: Requires os.environ["GOOGLE_API_KEY"] to be set
    
    agent = SignalCollectionAgent()
    
    # Test cases matching the exact user requirements
    test_signals = [
        "G-10 mein pani bhar gaya hai, please send help fast!",
        "Heavy rain expected in Lahore over the next 48 hours according to met office.",
        "Road blockage near Mall Road due to protest, traffic is completely jammed."
    ]
    
    print("--- CIRO Signal Collection Agent ---")
    for sig in test_signals:
        print(f"\n[Raw Input]: {sig}")
        parsed_output = agent.process_signal(sig)
        if parsed_output:
            print("[Structured JSON]:")
            # Outputting beautifully formatted JSON
            print(parsed_output.model_dump_json(indent=2))
