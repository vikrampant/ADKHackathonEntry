from .sub_agents import JobReqTitleChecker, JobReqDescriptionChecker, JobReqApproval
from google.adk.agents import SequentialAgent

class JobReqAgentOrchestrator:
    def __init__(self):
        # Root Agent
        self.root_agent = SequentialAgent(
            name="JobReqAgentOrchestrator",
            sub_agents=[JobReqTitleChecker, JobReqDescriptionChecker, JobReqApproval],
            description="Orchestrates the job requirement agents."
        )