import os
import json
import datetime
from typing import List, Dict, Literal, Any
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. Schemas (Inputs & Outputs)
# ------------------------------------------------------------------

# Input Schema (Data received from the Action Planning Agent)
class DispatchOrder(BaseModel):
    unit_type: str
    quantity: int
    destination: str
    priority: str

class ExecutionPlanInput(BaseModel):
    public_alert_message: str
    recommended_rerouting: str
    dispatched_units: List[DispatchOrder]
    step_by_step_sops: List[str]

# Output Schemas (Simulation Logging)
class ExecutionLog(BaseModel):
    timestamp_offset: str = Field(description="Time offset from start, e.g., '+00:01:23'")
    action_category: Literal["Dispatch", "MapUpdate", "SMSAlert", "TicketCreation", "Rerouting"]
    status: Literal["SUCCESS", "FAILED", "PENDING"]
    log_message: str = Field(description="Detailed technical log of the API call or action.")

class SystemState(BaseModel):
    available_fleet: Dict[str, int]
    active_map_pins: int
    sms_sent_count: int

class SimulationReport(BaseModel):
    before_state: SystemState
    after_state: SystemState
    execution_timeline: List[ExecutionLog] = Field(
        description="Chronological logs simulating the API executions."
    )
    dashboard_update_payload: str = Field(
        description="A JSON string representing the WebSocket payload to be pushed to the Frontend Dashboard."
    )

# ------------------------------------------------------------------
# 2. Simulation Architecture & Prompt Engine
# ------------------------------------------------------------------
SIMULATION_PROMPT = """
You are the Simulation & Execution Engine for CIRO. 
Your job is to take a validated Execution Plan and "simulate" the real-world API executions required to orchestrate the crisis response.

Input Execution Plan:
{plan_json}

Initial System State:
{initial_state_json}

Simulation Rules:
1. Dispatch: For every dispatched unit in the plan, subtract from the initial available fleet. Log the simulated dispatch API call (e.g., 'POST /api/fleet/dispatch -> 200 OK').
2. Ticket Creation: Simulate hitting a ticketing system (e.g., Jira or ServiceNow) for each SOP step.
3. Map Updates: Simulate the WebSocket broadcast for traffic rerouting and unit tracking. Increment 'active_map_pins'.
4. SMS Alerts: Simulate hitting the Twilio API to broadcast the public_alert_message. Set 'sms_sent_count' to 50000 (simulating affected population).
5. Inject Realism: Make 1 out of every 5 actions randomly "FAILED" (e.g., an SMS batch timeout) and automatically followed by a "SUCCESS" retry.

{format_instructions}

Generate the chronological execution logs and the before/after state diff.
"""

# ------------------------------------------------------------------
# 3. Agent Implementation
# ------------------------------------------------------------------
class SimulationExecutionAgent:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Flash is ideal here for fast generation of structured logs
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.4, # Slightly higher temperature to introduce realistic variance in logs
            max_retries=3
        )
        self.parser = PydanticOutputParser(pydantic_object=SimulationReport)
        
        self.prompt = PromptTemplate(
            template=SIMULATION_PROMPT,
            input_variables=["plan_json", "initial_state_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def execute_plan(self, plan: ExecutionPlanInput, initial_state: SystemState) -> Optional[SimulationReport]:
        """
        Event Execution Engine: Runs the simulation and returns the diff and logs.
        """
        try:
            plan_json = plan.model_dump_json()
            state_json = initial_state.model_dump_json()
            
            result = self.chain.invoke({
                "plan_json": plan_json,
                "initial_state_json": state_json
            })
            return result

        except ValidationError as ve:
            print(f"[Error] Simulation Format Validation Failed: {ve}")
            return None
        except Exception as e:
            print(f"[Error] Execution Engine Failure: {e}")
            return None

# ------------------------------------------------------------------
# 4. Usage & Execution Example
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = SimulationExecutionAgent()
    
    # Mock data coming from the Action Planning Agent
    action_plan = ExecutionPlanInput(
        public_alert_message="[URGENCY] G-10 Commercial Area Fire. Evacuate immediately.",
        recommended_rerouting="Blockade Kashmir Highway at G-10 intersection. Reroute via F-10.",
        dispatched_units=[
            DispatchOrder(unit_type="Fire Engine", quantity=4, destination="Sector G-10", priority="Immediate"),
            DispatchOrder(unit_type="Police Unit", quantity=2, destination="Kashmir Highway", priority="Immediate")
        ],
        step_by_step_sops=[
            "Establish perimeter 500m around G-10 Commercial.",
            "Deploy hazmat protocol due to proximity to gas station."
        ]
    )
    
    # Mock Database State BEFORE execution
    db_before_state = SystemState(
        available_fleet={"Fire Engine": 5, "Police Unit": 8, "Ambulance": 12},
        active_map_pins=12,
        sms_sent_count=1000
    )
    
    print("--- CIRO Simulation & Execution Engine ---")
    print("\n[Executing Plan...]")
    
    report = agent.execute_plan(action_plan, db_before_state)
    
    if report:
        print("\n[--- BEFORE VS AFTER STATE ---]")
        print(f"Before Fleet: {report.before_state.available_fleet}")
        print(f"After Fleet : {report.after_state.available_fleet}")
        
        print("\n[--- LIVE EXECUTION LOGS ---]")
        for log in report.execution_timeline:
            status_icon = "🟢" if log.status == "SUCCESS" else ("🔴" if log.status == "FAILED" else "🟡")
            print(f"[{log.timestamp_offset}] {status_icon} [{log.action_category}] : {log.log_message}")
        
        print("\n[--- DASHBOARD WEBSOCKET PAYLOAD ---]")
        print(report.dashboard_update_payload)
