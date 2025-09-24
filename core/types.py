"""
Shared data types and models for the Contract-Agent application
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class CrewProcessingResult:
    """Result from CrewAI contract processing workflow"""
    success: bool
    job_id: str
    final_rtf: Optional[str]
    original_rtf: str
    iterations_used: int
    total_processing_time: float
    final_score: Optional[float]
    crew_output: str
    error_message: Optional[str]
    chunk_processing_stats: Optional[Dict] = None
