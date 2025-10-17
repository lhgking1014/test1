from dataclasses import dataclass, field


@dataclass
class NewsItem:
    source: str
    title: str
    summary: str
    url: str
    published_at: str
    image_url: str | None = field(default=None)
    language: str | None = field(default=None)
    highlights: list[str] | None = field(default=None)
