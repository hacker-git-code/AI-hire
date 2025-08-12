from enum import Enum

class PipelineStage(str, Enum):
    """Pipeline stages for candidate progression."""
    SCREENING = "screening"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"

    @classmethod
    def get_next_stage(cls, current_stage: 'PipelineStage') -> 'PipelineStage':
        """Get the next stage in the pipeline."""
        stages = list(cls)
        try:
            current_index = stages.index(current_stage)
            if current_index < len(stages) - 1:
                return stages[current_index + 1]
        except ValueError:
            pass
        return current_stage

    @classmethod
    def get_previous_stage(cls, current_stage: 'PipelineStage') -> 'PipelineStage':
        """Get the previous stage in the pipeline."""
        stages = list(cls)
        try:
            current_index = stages.index(current_stage)
            if current_index > 0:
                return stages[current_index - 1]
        except ValueError:
            pass
        return current_stage

    @classmethod
    def is_valid_transition(cls, from_stage: 'PipelineStage', to_stage: 'PipelineStage') -> bool:
        """Check if the transition between stages is valid."""
        stages = list(cls)
        try:
            from_index = stages.index(from_stage)
            to_index = stages.index(to_stage)
            return abs(to_index - from_index) <= 1
        except ValueError:
            return False 