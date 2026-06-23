# backend/schemas/userSchemas.py
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    userId: str = Field(alias="user_id")
    username: str
    role: str

class RecommendationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str #
    type: Literal['review', 'practice'] #
    link: str #

class SkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str #
    progress: int #

class LastAccessedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    exerciseId: str = Field(alias="exercise_id") #
    title: str #
    topicName: str = Field(alias="topic_name") #
    progress: int #

class BehavioralMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    avgAttemptsPerExercise: float = Field(default=0.0, alias="avg_attempts_per_exercise") #
    hintsPerSuccessRatio: float = Field(default=0.0, alias="hints_per_success_ratio") #
    mostCommonErrorType: Optional[str] = Field(None, alias="most_common_error_type") #
    stuckProbability: float = Field(default=0.0, alias="stuck_probability") #

class UserStatsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    username: str #
    level: str #
    exercisesCompleted: int = Field(alias="exercises_completed") #
    studyStreak: int = Field(alias="study_streak") #
    totalHours: float = Field(alias="total_hours") #
    skills: List[SkillSchema] #
    lastAccessed: Optional[LastAccessedSchema] = None #
    dailyTip: str = Field(alias="daily_tip") #
    masteryScore: int = Field(alias="mastery_score") #
    weakAreas: List[str] = Field(alias="weak_areas") #
    strongAreas: List[str] = Field(alias="strong_areas") #
    recommendations: List[RecommendationSchema] #
    behavioralProfile: Optional[BehavioralMetrics] = Field(None, alias="behavioral_profile") #
    avgResolutionTime: float = Field(default=0.0, alias="avg_resolution_time") #