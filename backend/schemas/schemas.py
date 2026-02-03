# backend/schemas/schemas.py
from typing import Optional, Literal, List, Tuple, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Alias para el lenguaje
Lang = Literal["python", "java", "cpp"]

class ExecuteIn(BaseModel):
    user_id: str
    session_id: str
    exercise_id: str
    attempt_id: str
    code: str
    duration_ms: Optional[int] = 0

class ExecResult(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    error_type: Optional[str] = None
    runtime_ms: Optional[int] = None

class HintIn(BaseModel):
    user_id: str
    session_id: str
    exercise_id: str
    attempt_id: str
    code: str
    exec_result: Optional[ExecResult] = None
    lang: Optional[Lang] = "python"   # usa el alias

class HintOut(BaseModel):
    hint: str
    pattern_id: str
    concept: str = ""

# Para /api/cfg con lang en el body (si lo usas)
class CodeIn(BaseModel):
    code: str
    lang: Lang = "python"              # <-- corrige esto

# Para /api/cfg/{lang} con body { code }
class CodeOnly(BaseModel):
    code: str

class CFGOut(BaseModel):
    language: str
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Tuple[str, str]] = Field(default_factory=list)
    mermaid: Optional[str] = None

# ==========================================
# 4. SUB-ESQUEMAS PARA USER STATS (Orden Crítico)
# ==========================================
# Definimos estos primero para que UserStatsSchema pueda usarlos
class RecommendationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    type: Literal['review', 'practice']
    link: str

class SkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    progress: int

class LastAccessedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    exerciseId: str = Field(alias="exercise_id")
    title: str
    topicName: str = Field(alias="topic_name")
    progress: int
    
# --- Nuevos Schemas de Contenido (Traducción de tus interfaces de Angular) ---

class ExerciseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True) # <--- Crucial
    id: str
    topicId: str = Field(alias="topic_id") # Mapea topic_id de la DB
    title: str
    description: str
    difficulty: Literal['Fácil', 'Medio', 'Difícil']
    completed: bool = False

class TopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    title: str
    description: str
    icon: str
    progress: float = 0.0
    totalExercises: int = Field(alias="total_exercises") # Mapea total_exercises
    category: str
    tags: List[str]
    estimatedTime: str = Field(alias="estimated_time") # Mapea estimated_time

class LastAccessedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exerciseId: str = Field(alias="exercise_id")
    title: str
    topicName: str = Field(alias="topic_name")
    progress: int
    
    
#------------user-------------#

class BehavioralMetrics(BaseModel):
    """Métricas de proceso para Learning Analytics."""
    avg_attempts_per_exercise: float = 0.0
    hints_per_success_ratio: float = 0.0
    most_common_error_type: Optional[str] = None
    stuck_probability: float = 0.0  # Probabilidad de bloqueo (0.0 a 1.0)

class UserStatsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    username: str
    level: str
    exercisesCompleted: int = Field(alias="exercises_completed")
    studyStreak: int = Field(alias="study_streak")
    totalHours: float = Field(alias="total_hours")
    skills: List[SkillSchema]
    lastAccessed: Optional[LastAccessedSchema] = None
    dailyTip: str = Field(alias="daily_tip")
    masteryScore: int = Field(alias="mastery_score")
    weakAreas: List[str] = Field(alias="weak_areas")
    strongAreas: List[str] = Field(alias="strong_areas")
    recommendations: List[RecommendationSchema]
    behavioral_profile: Optional[BehavioralMetrics] = None
    avgResolutionTime: float = Field(alias="avg_resolution_time", default=0.0)
    