import os
import json
from typing import List, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. Schemas (Inputs & Outputs)
# ------------------------------------------------------------------

# Input Schema (Data received from the Crisis Detection Agent)
class CrisisEventInput(BaseModel):
    crisis_type: str
    affected_locations: List[str]
    base_severity_score: int
    reasoning: str

# Structured Output Schema for the Severity Analysis Agent
class SeverityAssessment(BaseModel):
    calculated_severity_score: int = Field(
        description="Final severity score (1-10) factoring in population, traffic, and time-critical urgency."
    )
    estimated_affected_population: int = Field(
        description="Estimated order of magnitude of affected people (e.g., 500, 10000, 500000) based on location density."
    )
    traffic_disruption_level: Literal["None", "Low", "Moderate", "High", "Critical"] = Field(
        description="Estimated disruption to local and regional traffic infrastructure."
    )
    emergency_urgency: Literal["Low", "Medium", "High", "Critical"] = Field(
        description="How quickly emergency services need to respond to prevent loss of life or catastrophic property damage."
    )
    escalation_level: Literal["Monitor", "Local Response", "City-wide Response", "National/Federal Emergency"] = Field(
        description="Recommended hierarchy of response escalation based on the impact."
    )
    impact_analysis: str = Field(
        description="A 2-3 sentence narrative describing the multifaceted impact of the crisis on the city/region."
    )
    reasoning_trace: List[str] = Field(
        description="An array of logical steps showing the thought process used to derive the final score and estimates."
    )

# ------------------------------------------------------------------
# 2. Reasoning Workflow & Prompt Engineering
# ------------------------------------------------------------------
SEVERITY_PROMPT = """
You are the Severity Analysis Agent for the CIRO platform. 
A localized crisis has been detected. Your task is to analyze the crisis, calculate the blast/impact radius, estimate the affected population, and determine the exact escalation protocol required.

Input Crisis Details (JSON):
{crisis_json}

Reasoning Algorithm & Workflow:
1. Demographic & Location Analysis: Based on the "affected_locations", estimate the general population density. A fire in a remote area has a lower impact than a fire in a dense commercial sector like "G-10" or "Downtown".
2. Traffic Matrix: Evaluate how the "crisis_type" affects infrastructure. Floods and Accidents severely disrupt traffic grids.
3. Urgency Calculation: Assess the immediate threat to life. Fire and Accidents are highly urgent (Critical). Weather alerts might be slower-moving (Medium/High).
4. Escalation Prioritization:
    - Base Severity 1-3 -> "Monitor" or "Local Response"
    - Base Severity 4-7 -> "Local Response" to "City-wide Response"
    - Base Severity 8-10 -> "City-wide Response" or "National/Federal Emergency"
5. Final Scoring: Adjust the `base_severity_score` up or down by 1-2 points based on the population density and traffic disruption you calculated.

{format_instructions}

Process the crisis data using the algorithm above and output the strict JSON.
"""

# ------------------------------------------------------------------
# 3. Agent Implementation
# ------------------------------------------------------------------
class SeverityAnalysisAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # Gemini 1.5 Pro is required for multi-step algorithmic reasoning
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0, 
            max_retries=3
        )
        self.parser = PydanticOutputParser(pydantic_object=SeverityAssessment)
        
        self.prompt = PromptTemplate(
            template=SEVERITY_PROMPT,
            input_variables=["crisis_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def analyze_severity(self, crisis_event: CrisisEventInput) -> Optional[SeverityAssessment]:
        """
        Takes a detected Crisis, runs the severity algorithms, and returns the Escalation Plan.
        """
        try:
            crisis_json = crisis_event.model_dump_json()
            result = self.chain.invoke({"crisis_json": crisis_json})
            return result

        except ValidationError as ve:
            print(f"[Error] Schema Validation Failed: {ve}")
            return None
        except Exception as e:
            print(f"[Error] Severity Analysis Failure: {e}")
            return None

# ------------------------------------------------------------------
# 4. Usage & Execution Example
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = SeverityAnalysisAgent()
    
    # Mock input received from the Crisis Detection Agent
    detected_crisis = CrisisEventInput(
        crisis_type="fire",
        affected_locations=["Sector G-10 Commercial Area", "Kashmir Highway"],
        base_severity_score=7,
        reasoning="Social media reports of smoke in G-10 corroborate with a traffic update showing jammed roads at the nearby highway turnoff, indicating a localized fire incident."
    )
    
    print("--- CIRO Severity Analysis Agent ---")
    print("\n[Input Crisis Event]:")
    print(detected_crisis.model_dump_json(indent=2))
    
    print("\n[Analyzing Impact & Calculating Escalation...]")
    assessment = agent.analyze_severity(detected_crisis)
    
    if assessment:
        print("\n[Final Severity Assessment Result]:")
        print(assessment.model_dump_json(indent=2))
        
        print(f"\n🚨 ACTION REQUIRED: Proceeding to Action Planning Agent with Escalation Level: [{assessment.escalation_level.upper()}]")
