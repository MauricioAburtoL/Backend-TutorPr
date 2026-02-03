# backend/schemas/courseSchemas.py
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

class ExerciseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str #
    topicId: str = Field(alias="topic_id") #
    title: str #
    description: str #
    difficulty: Literal['Fácil', 'Medio', 'Difícil'] #
    completed: bool = False #

class TopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str #
    title: str #
    description: str #
    icon: str #
    progress: float = 0.0 #
    totalExercises: int = Field(alias="total_exercises") #
    category: str #
    tags: List[str] #
    estimatedTime: str = Field(alias="estimated_time") #