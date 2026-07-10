from dataclasses import dataclass, field


@dataclass
class Candidate:
    source: str
    source_ref: str
    title: str
    url: str
    summary: str
    engagement: dict = field(default_factory=dict)
    topic_tags: list[str] = field(default_factory=list)
    emotional_driver: str | None = None
    news_hook: str | None = None
    predicted_relevance: float | None = None
