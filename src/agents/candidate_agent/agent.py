from .sub_agents.candidateLocationReview import CandidateLocationReview
from .sub_agents.candidateExperienceReview import CandidateExperienceReview
from .sub_agents.candidateSkillReview import CandidateSkillReview
from .sub_agents.candidateInstantFeedbackProcessor import CandidateInstantFeedbackProcessor
from google.adk.agents import SequentialAgent

class CandidateAgentOrchestrator:
    def __init__(self):
        # Root Agent
        self.root_agent = SequentialAgent(
            name="CandidateAgentOrchestrator",
            sub_agents=[CandidateLocationReview, CandidateExperienceReview, CandidateSkillReview, CandidateInstantFeedbackProcessor],
            description="Orchestrates the candidate agents."
        )