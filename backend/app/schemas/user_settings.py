from pydantic import BaseModel, Field


class UserSettingsOut(BaseModel):
    weight_base: float = 1.0
    weight_log_multiplier: float = 0.5
    relevance_llm_weight: float = 1.0
    relevance_learning_weight: float = 1.0
    relevance_cluster_weight: float = 0.5
    stats_enabled: bool = True
    output_language: str | None = None
    time_decay_param: float = 2.0
    show_decay_param: float = 0.0
    mark_shown_delay_seconds: int = 5
    learning_window_days: int = 90
    ignore_penalty_weight: float = 0.1

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    weight_base: float | None = Field(None, ge=0.0, le=10.0)
    weight_log_multiplier: float | None = Field(None, ge=0.0, le=5.0)
    relevance_llm_weight: float | None = Field(None, ge=0.0, le=5.0)
    relevance_learning_weight: float | None = Field(None, ge=0.0, le=5.0)
    relevance_cluster_weight: float | None = Field(None, ge=0.0, le=5.0)
    stats_enabled: bool | None = None
    output_language: str | None = Field(None, max_length=10)
    time_decay_param: float | None = Field(None, ge=0.0, le=20.0)
    show_decay_param: float | None = Field(None, ge=0.0, le=10.0)
    mark_shown_delay_seconds: int | None = Field(None, ge=1, le=60)
    learning_window_days: int | None = Field(None, ge=0, le=3650)
    ignore_penalty_weight: float | None = Field(None, ge=0.0, le=5.0)
