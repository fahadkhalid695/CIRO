import os
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. Schemas (Inputs & Outputs)
# ------------------------------------------------------------------

# Input Schema (Data received from the Signal Collection Agent)
class SignalInput(BaseModel):
    normalized_text: str
    location: Optional[str]
    urgency_level: str
    source_classification: str
    confidence_score: float

# Structured Output Schema for the Crisis Detection Agent
class CrisisEvent(BaseModel):
    is_crisis_detected: bool = Field(
        description="True if the combination of signals indicates an actual crisis, False if it's just noise or isolated incidents."
    )
    crisis_type: Optional[Literal["flood", "accident", "heatwave", "infrastructure failure", "fire", "traffic congestion"]] = Field(
        description="The specific category of the crisis. Null if no crisis is detected."
    )
    severity_score: int = Field(
        description="Calculated severity from 1 to 10. 10 being catastrophic."
    )
    confidence: float = Field(
        description="Overall confidence in this detection (0.0 to 1.0). High if multiple independent sources corroborate."
    )
    affected_locations: List[str] = Field(
        description="List of all geographic locations that appear to be impacted."
    )
    reasoning: str = Field(
        description="A 1-2 sentence explanation of WHY these signals were correlated into a crisis, showing the AI's thought process."
    )

# ------------------------------------------------------------------
# 2. Reasoning Workflow & Prompt Engineering
# ------------------------------------------------------------------
DETECTION_PROMPT = """
You are the Crisis Detection Agent for CIRO. 
Your task is to analyze an incoming batch of structured intelligence signals (collected over a short time window) and determine if they collectively indicate a localized crisis.

Input Signals (JSON):
{signals_json}

Reasoning Workflow:
1. Signal Correlation: Look for intersecting locations or themes (e.g., a "traffic update" about jammed roads + a "social media" post about smoke).
2. Anomaly Detection: Distinguish between isolated everyday events (like a cat in a tree) and part of a larger systemic failure.
3. Severity Scoring System: 
   - 1-3: Minor disruption
   - 4-6: Moderate impact (e.g., major traffic congestion)
   - 7-8: High threat (e.g., active fire)
   - 9-10: Catastrophic threat to life
4. Confidence Calculation: Base your confidence (0.0-1.0) on the volume and corroboration of the signals. If 3 different sources report the same/related things at the same location, confidence is > 0.9.

Edge Case Handling:
- Disjointed Geography: If signals are highly urgent but geographically distant, they DO NOT constitute a single crisis. Ignore the outliers.
- Contradictory Signals: If signals contradict each other, lower the confidence score significantly.

{format_instructions}

Analyze the signals and output the structured JSON.
"""

# ------------------------------------------------------------------
# 3. Detection Pipeline Implementation
# ------------------------------------------------------------------
class CrisisDetectionAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # We use Gemini 1.5 Pro here instead of Flash because correlating multiple 
        # complex signals requires advanced reasoning capabilities.
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0, 
            max_retries=3
        )
        self.parser = PydanticOutputParser(pydantic_object=CrisisEvent)
        
        self.prompt = PromptTemplate(
            template=DETECTION_PROMPT,
            input_variables=["signals_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def evaluate_signals(self, signals: List[SignalInput]) -> Optional[CrisisEvent]:
        """
        Detection Pipeline: Takes a list of signals, converts to JSON, feeds to LLM, returns CrisisEvent.
        """
        try:
            # Convert signal objects to JSON strings for the prompt
            signals_dict_list = [sig.model_dump() for sig in signals]
            signals_json = str(signals_dict_list)
            
            # Execute reasoning chain
            result = self.chain.invoke({"signals_json": signals_json})
            
            return result

        except ValidationError as ve:
            print(f"[Error] Failed to format Crisis Event: {ve}")
            return None
        except Exception as e:
            print(f"[Error] Detection Pipeline Failure: {e}")
            return None

# ------------------------------------------------------------------
# 4. Usage & Execution
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Note: Requires os.environ["GOOGLE_API_KEY"] to be set
    
    agent = CrisisDetectionAgent()
    
    # Simulating a batch of signals hitting the system within a 5-minute window
    incoming_signals = [
        SignalInput(
            normalized_text="Thick black smoke seen rising near Sector G-10.",
            location="Sector G-10",
            urgency_level="High",
            source_classification="Social Media",
            confidence_score=0.85
        ),
        SignalInput(
            normalized_text="Traffic completely jammed on Kashmir Highway near G-10 turnoff.",
            location="Kashmir Highway, G-10",
            urgency_level="Medium",
            source_classification="Traffic Update",
            confidence_score=0.9
        ),
        SignalInput(
            normalized_text="Heatwave warning in effect for the capital region.",
            location="Capital Region",
            urgency_level="Medium",
            source_classification="Weather Alert",
            confidence_score=0.99
        ),
        SignalInput(
            normalized_text="My cat is stuck in a tree at F-8 park.",
            location="Sector F-8",
            urgency_level="Low",
            source_classification="Emergency Complaint",
            confidence_score=0.6
        )
    ]
    
    print("--- CIRO Crisis Detection Agent ---")
    detected_crisis = agent.evaluate_signals(incoming_signals)
    
    if detected_crisis:
        print("\n[Detection Result]:")
        print(detected_crisis.model_dump_json(indent=2))
        
        if detected_crisis.is_crisis_detected:
            print(f"\n🚀 CRISIS CONFIRMED: Triggering Severity Analysis Agent for '{detected_crisis.crisis_type}'...")
        else:
            print("\n💤 No cohesive crisis detected from current signals.")
