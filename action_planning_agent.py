import os
import json
from typing import List, Dict, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. Schemas (Inputs & Outputs)
# ------------------------------------------------------------------

# Input Schema (Aggregated state passed to the Planning Agent)
class PlanningInput(BaseModel):
    crisis_type: str
    severity_score: int
    affected_locations: List[str]
    available_resources: Dict[str, int] = Field(
        description="A dictionary of available units (e.g., {'Fire Engines': 5, 'Ambulances': 12})"
    )

# Sub-schema for individual dispatches
class DispatchOrder(BaseModel):
    unit_type: str = Field(description="Type of emergency vehicle/unit.")
    quantity: int = Field(description="Number of units to dispatch. MUST NOT exceed available_resources.")
    destination: str = Field(description="Target location for these units.")
    priority: Literal["Immediate", "Secondary", "Standby"]

# Structured Output Schema for the Action Planning Agent
class ExecutionPlan(BaseModel):
    public_alert_message: str = Field(
        description="A concise, actionable 160-character alert message to broadcast to civilians via push notification/SMS."
    )
    recommended_rerouting: str = Field(
        description="Specific instructions for traffic rerouting away from the affected locations."
    )
    dispatched_units: List[DispatchOrder] = Field(
        description="Array of precise dispatch orders. You must strictly budget against the available_resources."
    )
    step_by_step_sops: List[str] = Field(
        description="Chronological, prioritized Standard Operating Procedures (SOPs) for the command center to follow."
    )
    reasoning_pipeline: str = Field(
        description="Explanation of the decision tree used to allocate these specific resources based on the severity score."
    )

# ------------------------------------------------------------------
# 2. Decision Tree & Prompt Engineering Strategy
# ------------------------------------------------------------------
PLANNING_PROMPT = """
You are the Action Planning Agent for CIRO. 
A highly severe crisis has been vetted. Your task is to act as the tactical commander. You must generate a precise execution plan.

Input Context (JSON):
{planning_json}

Planning Algorithms & Decision Tree:
1. Resource Allocation Constraints: You CANNOT dispatch more units than are listed in "available_resources". 
   - If Severity > 8: Commit up to 80% of available resources.
   - If Severity 5-7: Commit up to 40% of available resources.
   - If Severity < 5: Commit minimal resources (1-2 units) to investigate.
2. Unit Prioritization (Based on Crisis Type):
   - Fire -> Prioritize Fire Engines, then Ambulances, then Police for perimeter.
   - Accident -> Prioritize Ambulances and Police, Fire Engines secondary (for jaws of life/spills).
   - Traffic Congestion -> Prioritize Police only.
3. Rerouting Logic: Identify the "affected_locations" and explicitly state a perimeter or alternate route.
4. Public Alert Formulation: Must be direct. Format: [URGENCY] [LOCATION] [ACTION REQUIRED]. 

{format_instructions}

Execute the planning algorithms and output the strict JSON format.
"""

# ------------------------------------------------------------------
# 3. Agent Implementation
# ------------------------------------------------------------------
class ActionPlanningAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # We use Gemini 1.5 Pro because complex constraint solving 
        # (resource budgeting) requires advanced context windows and reasoning.
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0, 
            max_retries=3
        )
        self.parser = PydanticOutputParser(pydantic_object=ExecutionPlan)
        
        self.prompt = PromptTemplate(
            template=PLANNING_PROMPT,
            input_variables=["planning_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_plan(self, planning_state: PlanningInput) -> str | ExecutionPlan | None:
        """
        Takes the crisis severity and available fleet, and outputs an executable Plan.
        """
        try:
            planning_json = planning_state.model_dump_json()
            result = self.chain.invoke({"planning_json": planning_json})
            return result

        except ValidationError as ve:
            print(f"[Error] Schema Validation Failed during Planning: {ve}")
            return None
        except Exception as e:
            print(f"[Error] Action Planning Failure: {e}")
            return None

# ------------------------------------------------------------------
# 4. Usage & Execution Example
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = ActionPlanningAgent()
    
    # Mock aggregated state arriving from the Severity Agent and a Database lookup
    current_state = PlanningInput(
        crisis_type="fire",
        severity_score=8,
        affected_locations=["Sector G-10 Commercial Area"],
        available_resources={
            "Fire Engines": 5,
            "Ambulances": 12,
            "Police Units": 8,
            "Hazmat Teams": 2
        }
    )
    
    print("--- CIRO Action Planning Agent ---")
    print("\n[Input State & Fleet Resources]:")
    print(current_state.model_dump_json(indent=2))
    
    print("\n[Generating Tactical Execution Plan...]")
    plan = agent.generate_plan(current_state)
    
    if plan:
        print("\n[Final Execution Plan Result]:")
        print(plan.model_dump_json(indent=2))
        
        print("\n✅ PLAN GENERATED: Ready for 'Simulation & Execution Agent' to dispatch units via WebSocket.")
