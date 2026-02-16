#!/usr/bin/env python3
"""
AEGIS - Job Manager Module
=====================================
Version: reads from version.json (module v1.0)

Provides async job management with phase-based progress tracking for long-running
operations like document review.

Features:
- Job queue with unique job_id generation
- Phase-based progress tracking (extract → parse → checkers → postprocess → export)
- Status polling endpoint support
- Elapsed time and ETA calculation
- Job cancellation support
- Thread-safe job storage

Created for Thread 8: Job/Progress System
"""

import uuid
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

__version__ = "1.0.0"


class JobPhase(Enum):
    """Processing phases for document review."""
    QUEUED = "queued"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    PARSING = "parsing"
    CHECKING = "checking"
    POSTPROCESSING = "postprocessing"
    EXPORTING = "exporting"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(Enum):
    """Overall job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Phase weights for progress calculation (total = 100)
PHASE_WEIGHTS = {
    JobPhase.QUEUED: 0,
    JobPhase.UPLOADING: 5,
    JobPhase.EXTRACTING: 15,
    JobPhase.PARSING: 10,
    JobPhase.CHECKING: 50,
    JobPhase.POSTPROCESSING: 15,
    JobPhase.EXPORTING: 5,
    JobPhase.COMPLETE: 100,
    JobPhase.FAILED: 0,
    JobPhase.CANCELLED: 0,
}

# Cumulative progress at start of each phase
PHASE_PROGRESS_START = {
    JobPhase.QUEUED: 0,
    JobPhase.UPLOADING: 0,
    JobPhase.EXTRACTING: 5,
    JobPhase.PARSING: 20,
    JobPhase.CHECKING: 30,
    JobPhase.POSTPROCESSING: 80,
    JobPhase.EXPORTING: 95,
    JobPhase.COMPLETE: 100,
}


@dataclass
class JobProgress:
    """Progress tracking for a job."""
    phase: JobPhase = JobPhase.QUEUED
    phase_progress: float = 0.0  # 0-100 within current phase
    overall_progress: float = 0.0  # 0-100 overall
    current_checker: Optional[str] = None
    checkers_completed: int = 0
    checkers_total: int = 0
    last_log: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "phase_progress": round(self.phase_progress, 1),
            "overall_progress": round(self.overall_progress, 1),
            "current_checker": self.current_checker,
            "checkers_completed": self.checkers_completed,
            "checkers_total": self.checkers_total,
            "last_log": self.last_log
        }


@dataclass
class Job:
    """Represents a background job."""
    job_id: str
    job_type: str  # 'review', 'export', 'hyperlink_check', etc.
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = field(default_factory=JobProgress)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _cancelled: bool = False
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.started_at is None:
            return 0.0
        end_time = self.completed_at or time.time()
        return end_time - self.started_at
    
    @property
    def elapsed_formatted(self) -> str:
        """Get formatted elapsed time (e.g., '1m 23s')."""
        elapsed = self.elapsed_seconds
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds}s"
    
    @property
    def eta_seconds(self) -> Optional[float]:
        """Estimate remaining time based on progress."""
        if self.progress.overall_progress <= 0:
            return None
        if self.progress.overall_progress >= 100:
            return 0.0
        elapsed = self.elapsed_seconds
        if elapsed <= 0:
            return None
        # Linear estimate based on progress
        rate = self.progress.overall_progress / elapsed  # progress per second
        remaining_progress = 100 - self.progress.overall_progress
        return remaining_progress / rate if rate > 0 else None
    
    @property
    def eta_formatted(self) -> Optional[str]:
        """Get formatted ETA (e.g., '~2m 15s')."""
        eta = self.eta_seconds
        if eta is None:
            return None
        if eta < 60:
            return f"~{int(eta)}s"
        minutes = int(eta // 60)
        seconds = int(eta % 60)
        return f"~{minutes}m {seconds}s"
    
    @property
    def is_cancelled(self) -> bool:
        """Check if job was cancelled."""
        return self._cancelled
    
    def cancel(self):
        """Mark job as cancelled."""
        self._cancelled = True
        self.status = JobStatus.CANCELLED
        self.progress.phase = JobPhase.CANCELLED
        self.completed_at = time.time()
    
    def to_dict(self, include_result: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        data = {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress": self.progress.to_dict(),
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
            "elapsed": self.elapsed_formatted,
            "eta": self.eta_formatted,
            "error": self.error,
            "metadata": self.metadata
        }
        if include_result and self.result is not None:
            data["result"] = self.result
        return data


class JobManager:
    """
    Thread-safe job manager for background operations.
    
    Usage:
        manager = JobManager()
        job_id = manager.create_job('review', metadata={'filename': 'doc.docx'})
        
        # In worker thread:
        job = manager.get_job(job_id)
        manager.start_job(job_id)
        manager.update_phase(job_id, JobPhase.EXTRACTING)
        manager.update_checker_progress(job_id, 'grammar', 5, 20)
        manager.complete_job(job_id, result={'issues': [...]})
    """
    
    def __init__(self, max_jobs: int = 100, job_ttl: float = 3600):
        """
        Initialize job manager.
        
        Args:
            max_jobs: Maximum jobs to keep in memory
            job_ttl: Time-to-live for completed jobs (seconds)
        """
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.RLock()
        self._max_jobs = max_jobs
        self._job_ttl = job_ttl
    
    def create_job(self, job_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            job_type: Type of job ('review', 'export', etc.)
            metadata: Optional metadata (filename, options, etc.)
        
        Returns:
            Unique job ID
        """
        with self._lock:
            # Clean up old jobs if at capacity
            self._cleanup_old_jobs()
            
            job_id = str(uuid.uuid4())[:8]  # Short ID for readability
            job = Job(
                job_id=job_id,
                job_type=job_type,
                metadata=metadata or {}
            )
            self._jobs[job_id] = job
            return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def start_job(self, job_id: str) -> bool:
        """Mark job as started."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            job.progress.phase = JobPhase.QUEUED
            return True
    
    def update_phase(self, job_id: str, phase: JobPhase, log_message: Optional[str] = None) -> bool:
        """
        Update job to a new phase.
        
        Args:
            job_id: Job ID
            phase: New phase
            log_message: Optional log message
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.progress.phase = phase
            job.progress.phase_progress = 0.0
            job.progress.overall_progress = PHASE_PROGRESS_START.get(phase, 0)
            
            if log_message:
                job.progress.last_log = log_message
            
            return True
    
    def update_phase_progress(self, job_id: str, progress: float, log_message: Optional[str] = None) -> bool:
        """
        Update progress within current phase (0-100).
        
        Args:
            job_id: Job ID
            progress: Progress within phase (0-100)
            log_message: Optional log message
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.progress.phase_progress = min(100, max(0, progress))
            
            # Calculate overall progress
            phase = job.progress.phase
            phase_start = PHASE_PROGRESS_START.get(phase, 0)
            phase_weight = PHASE_WEIGHTS.get(phase, 0)
            
            # Add portion of current phase to overall
            phase_contribution = (job.progress.phase_progress / 100) * phase_weight
            job.progress.overall_progress = phase_start + phase_contribution
            
            if log_message:
                job.progress.last_log = log_message
            
            return True
    
    def update_checker_progress(self, job_id: str, checker_name: str, 
                                 completed: int, total: int) -> bool:
        """
        Update checker progress during CHECKING phase.
        
        Args:
            job_id: Job ID
            checker_name: Current checker name
            completed: Number of checkers completed
            total: Total number of checkers
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.progress.current_checker = checker_name
            job.progress.checkers_completed = completed
            job.progress.checkers_total = total
            
            # Calculate phase progress based on checker completion
            if total > 0:
                phase_progress = (completed / total) * 100
                return self.update_phase_progress(
                    job_id, 
                    phase_progress,
                    f"Running {checker_name}..."
                )
            
            return True
    
    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark job as complete with optional result.
        
        Args:
            job_id: Job ID
            result: Job result data
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.status = JobStatus.COMPLETE
            job.progress.phase = JobPhase.COMPLETE
            job.progress.overall_progress = 100
            job.progress.phase_progress = 100
            job.completed_at = time.time()
            job.result = result
            job.progress.last_log = "Complete"
            
            return True
    
    def fail_job(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed with error message.
        
        Args:
            job_id: Job ID
            error: Error message
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.status = JobStatus.FAILED
            job.progress.phase = JobPhase.FAILED
            job.completed_at = time.time()
            job.error = error
            job.progress.last_log = f"Error: {error}"
            
            return True
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
                return False
            
            job.cancel()
            return True
    
    def list_jobs(self, status: Optional[JobStatus] = None, 
                   job_type: Optional[str] = None,
                   limit: int = 20) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering.
        
        Args:
            status: Filter by status
            job_type: Filter by job type
            limit: Maximum results
        
        Returns:
            List of job dictionaries
        """
        with self._lock:
            jobs = list(self._jobs.values())
            
            # Filter
            if status:
                jobs = [j for j in jobs if j.status == status]
            if job_type:
                jobs = [j for j in jobs if j.job_type == job_type]
            
            # Sort by created_at descending
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            
            # Limit
            jobs = jobs[:limit]
            
            return [j.to_dict() for j in jobs]
    
    def _cleanup_old_jobs(self):
        """Remove old completed jobs."""
        with self._lock:
            now = time.time()
            to_remove = []
            
            for job_id, job in self._jobs.items():
                # Remove completed/failed jobs older than TTL
                if job.status in (JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED):
                    if job.completed_at and (now - job.completed_at) > self._job_ttl:
                        to_remove.append(job_id)
            
            for job_id in to_remove:
                del self._jobs[job_id]
            
            # If still over capacity, remove oldest completed jobs
            if len(self._jobs) >= self._max_jobs:
                completed = [(jid, j) for jid, j in self._jobs.items() 
                            if j.status in (JobStatus.COMPLETE, JobStatus.FAILED)]
                completed.sort(key=lambda x: x[1].completed_at or 0)
                
                while len(self._jobs) >= self._max_jobs and completed:
                    jid, _ = completed.pop(0)
                    del self._jobs[jid]


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


# =============================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# =============================================================================

def create_review_job(filename: str, options: Optional[Dict] = None) -> str:
    """
    Create a new review job.
    
    Args:
        filename: Document filename
        options: Review options
    
    Returns:
        Job ID
    """
    manager = get_job_manager()
    return manager.create_job('review', metadata={
        'filename': filename,
        'options': options or {}
    })


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a job.
    
    Args:
        job_id: Job ID
    
    Returns:
        Job status dict or None if not found
    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if job:
        return job.to_dict()
    return None


def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full job result including result data.
    
    Args:
        job_id: Job ID
    
    Returns:
        Job dict with result or None
    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if job:
        return job.to_dict(include_result=True)
    return None


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print(f"Job Manager Module v{__version__}")
    print("=" * 50)
    
    # Test job lifecycle
    manager = get_job_manager()
    
    # Create job
    job_id = manager.create_job('review', {'filename': 'test.docx'})
    print(f"Created job: {job_id}")
    
    # Start job
    manager.start_job(job_id)
    print(f"Started job")
    
    # Simulate phases
    import time as t
    
    manager.update_phase(job_id, JobPhase.EXTRACTING, "Extracting text...")
    t.sleep(0.1)
    print(f"Phase: EXTRACTING - {manager.get_job(job_id).to_dict()['progress']}")
    
    manager.update_phase(job_id, JobPhase.PARSING, "Parsing document...")
    manager.update_phase_progress(job_id, 50, "Halfway through parsing")
    t.sleep(0.1)
    print(f"Phase: PARSING - {manager.get_job(job_id).to_dict()['progress']}")
    
    manager.update_phase(job_id, JobPhase.CHECKING)
    for i in range(5):
        manager.update_checker_progress(job_id, f"checker_{i}", i + 1, 5)
        t.sleep(0.05)
    print(f"Phase: CHECKING - {manager.get_job(job_id).to_dict()['progress']}")
    
    # Complete
    manager.complete_job(job_id, {'issues': [], 'score': 95})
    job = manager.get_job(job_id)
    print(f"\nCompleted job:")
    print(f"  Status: {job.status.value}")
    print(f"  Elapsed: {job.elapsed_formatted}")
    print(f"  Progress: {job.progress.overall_progress}%")
    
    print("\n✓ Job Manager test complete")
