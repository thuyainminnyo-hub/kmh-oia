"""Evidence-informed learning strategy primitives; not a learner diagnosis or ranking."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Strategy(str, Enum):
    RETRIEVAL = "retrieval"
    DISTRIBUTED = "distributed"
    INTERLEAVED = "interleaved"
    ELABORATION = "elaboration"
    DUAL_CODING = "dual_coding"


class FeedbackTiming(str, Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    NONE = "none"


@dataclass(frozen=True)
class StrategyGuidance:
    strategy: Strategy
    purpose: str
    learner_activity: str
    boundary_condition: str
    evidence_strength: str


GUIDANCE: dict[Strategy, StrategyGuidance] = {
    Strategy.RETRIEVAL: StrategyGuidance(
        Strategy.RETRIEVAL,
        "Strengthen recall of previously taught material.",
        "Ask the learner to recall or answer before showing the source material.",
        "Match practice and assessment format to the intended knowledge; retrieval alone may not ensure transfer.",
        "Supported by classroom meta-analysis; average effect is context-dependent.",
    ),
    Strategy.DISTRIBUTED: StrategyGuidance(
        Strategy.DISTRIBUTED,
        "Revisit the same learning material across separate sessions.",
        "Schedule short review sessions with an explicit retention target.",
        "Choose intervals in relation to the intended retention period; do not assume one universal schedule.",
        "Supported by classroom meta-analysis; spacing interval and comparison matter.",
    ),
    Strategy.INTERLEAVED: StrategyGuidance(
        Strategy.INTERLEAVED,
        "Help learners discriminate between related problem types.",
        "Mix related question types after initial instruction.",
        "Use only when learners have enough initial knowledge to make meaningful comparisons; evaluate feedback timing locally.",
        "Supported by classroom meta-analysis; feedback timing is a moderator requiring further study.",
    ),
    Strategy.ELABORATION: StrategyGuidance(
        Strategy.ELABORATION,
        "Connect new material to explanations and prior knowledge.",
        "Ask the learner to explain why an answer is correct and provide an example.",
        "Check explanations for accuracy; prompts should not reward fluent but incorrect reasoning.",
        "Established learning-science strategy; evaluate against the course outcome.",
    ),
    Strategy.DUAL_CODING: StrategyGuidance(
        Strategy.DUAL_CODING,
        "Coordinate complementary verbal and visual representations.",
        "Pair concise text with a relevant diagram, timeline, or worked visual.",
        "Visuals must add relevant information rather than decorative cognitive load.",
        "Use when the visual representation genuinely complements the content.",
    ),
}


@dataclass(frozen=True)
class RevisionPlan:
    """Educator-configured intervals; the engine does not infer an optimal schedule."""
    intervals_days: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.intervals_days:
            raise ValueError("at least one revision interval is required")
        if any(isinstance(day, bool) or not isinstance(day, int) or day <= 0
               for day in self.intervals_days):
            raise ValueError("revision intervals must be positive integer days")
        if tuple(sorted(set(self.intervals_days))) != self.intervals_days:
            raise ValueError("revision intervals must be unique and ascending")


def get_strategy_guidance(strategy: Strategy) -> StrategyGuidance:
    if not isinstance(strategy, Strategy):
        raise TypeError("strategy must be a Strategy value")
    return GUIDANCE[strategy]


def build_revision_plan(intervals_days: tuple[int, ...]) -> RevisionPlan:
    """Validate an educator/course-authored schedule without personal profiling."""
    return RevisionPlan(intervals_days=intervals_days)


def select_feedback_timing(timing: FeedbackTiming) -> FeedbackTiming:
    """Preserve an educator-selected feedback policy; do not assert one is universally best."""
    if not isinstance(timing, FeedbackTiming):
        raise TypeError("timing must be a FeedbackTiming value")
    return timing
