import os
import json
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# ------------------------------------------------------------------
# 1. Schemas (Dashboard Data Structures & Reports)
# ------------------------------------------------------------------

class TimelineEvent(BaseModel):
    timestamp_offset: str = Field(description="Time elapsed since crisis start (e.g., T+00:05)")
    actor: Literal["Signal Agent", "Detection Agent", "Severity Agent", "Action Agent", "Execution Engine"] = Field(
        description="Which node in the system performed the action."
    )
    action_summary: str = Field(description="A concise summary of what occurred at this timestamp.")

class SystemImprovement(BaseModel):
    area_of_improvement: str = Field(description="e.g., 'Response Time', 'Resource Allocation', 'False Positive Rate'")
    ai_recommendation: str = Field(description="Actionable advice for command staff to improve future responses.")

class FinalReport(BaseModel):
    executive_summary: str = Field(
        description="A 3-4 sentence high-level overview of the crisis, the response, and the outcome."
    )
    ai_reasoning_trace: List[str] = Field(
        description="A clear, human-readable trace of WHY the AI system made its core decisions."
    )
    timeline: List[TimelineEvent] = Field(
        description="Chronological timeline architecture of the entire automated response."
    )
    outcome_summary: str = Field(
        description="Summary of the execution results (e.g., fires contained, traffic cleared)."
    )
    system_improvements: List[SystemImprovement] = Field(
        description="AI-generated recommendations for systemic improvement based on execution logs."
    )
    exportable_markdown_report: str = Field(
        description="A beautifully formatted Markdown string of the entire report, ready for PDF export or email."
    )

# ------------------------------------------------------------------
# 2. Reporting Workflow & Prompt Engineering
# ------------------------------------------------------------------
REPORTING_PROMPT = """
You are the Post-Mortem Reporting Agent for CIRO. 
A crisis has been resolved. You are provided with the raw JSON logs of the entire multi-agent lifecycle (from initial signal ingestion to final execution).
Your job is to synthesize this data into a structured dashboard payload and a formal after-action report.

RAW SYSTEM LOGS:
{system_logs_json}

Workflow Instructions:
1. Summarize: Distill the noise into a clean Executive Summary.
2. Trace Reasoning: Extract the core logic used by the Detection and Severity agents to justify the escalation. This builds trust with human reviewers.
3. Build the Timeline: Extract key milestones and format them as T+ offsets.
4. Visualize Improvements: Analyze the "Execution" failures (if any) and suggest structural improvements. If resources ran too low, suggest expanding fleet capacity.
5. Markdown Export: Generate a comprehensive markdown document containing headers, bullet points, and the timeline, ready to be handed to a human Mayor or Fire Chief.

{format_instructions}

Process the raw logs and return the comprehensive JSON payload.
"""

# ------------------------------------------------------------------
# 3. Agent Implementation
# ------------------------------------------------------------------
class ReportingAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # Pro model is required here as it must ingest a massive context 
        # window of logs and perform complex summarization.
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2, 
            max_retries=3
        )
        self.parser = PydanticOutputParser(pydantic_object=FinalReport)
        
        self.prompt = PromptTemplate(
            template=REPORTING_PROMPT,
            input_variables=["system_logs_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_post_mortem(self, all_agent_logs: Dict[str, Any]) -> Optional[FinalReport]:
        """
        Takes the massive dictionary of every previous agent's output and synthesizes the final report.
        """
        try:
            logs_json = json.dumps(all_agent_logs)
            result = self.chain.invoke({"system_logs_json": logs_json})
            return result

        except ValidationError as ve:
            print(f"[Error] Report Generation Validation Failed: {ve}")
            return None
        except Exception as e:
            print(f"[Error] Reporting Agent Failure: {e}")
            return None

# ------------------------------------------------------------------
# 4. Usage & Execution Example
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = ReportingAgent()
    
    # Mocking the aggregated output of the entire multi-agent system
    mock_system_history = {
        "SignalCollection": {
            "inputs": ["Thick black smoke in G-10", "Traffic jammed at Kashmir Highway"],
            "urgency": "High"
        },
        "CrisisDetection": {
            "crisis_type": "fire",
            "confidence": 0.95,
            "reasoning": "Correlated social smoke with highway traffic cams."
        },
        "SeverityAnalysis": {
            "severity_score": 8,
            "escalation_level": "City-wide Response",
            "impact_analysis": "Major fire in commercial zone risking adjacent highway gridlock."
        },
        "ActionPlanning": {
            "dispatched": [{"type": "Fire Engine", "quantity": 4}],
            "sms_alert": "G-10 Fire. Evacuate."
        },
        "ExecutionEngine": {
            "logs": [
                {"time": "T+00:01", "action": "MapUpdate", "status": "SUCCESS"},
                {"time": "T+00:03", "action": "SMSAlert", "status": "FAILED", "note": "Gateway timeout"},
                {"time": "T+00:04", "action": "SMSAlert", "status": "SUCCESS", "note": "Retry successful"}
            ],
            "final_fleet_status": {"Fire Engine": 1}
        }
    }
    
    print("--- CIRO Reporting & Analytics Agent ---")
    print("\n[Synthesizing Post-Mortem Report from System Logs...]")
    
    report = agent.generate_post_mortem(mock_system_history)
    
    if report:
        print("\n[--- DASHBOARD JSON DATA STRUCTURE ---]")
        print(f"Timeline Events Extracted: {len(report.timeline)}")
        print(f"Improvements Suggested: {len(report.system_improvements)}")
        
        print("\n[--- EXPORTABLE MARKDOWN REPORT (Preview) ---]")
        # This string can be saved directly to an S3 bucket or emailed
        print(report.exportable_markdown_report[:500] + "...\n(Truncated for preview)")
