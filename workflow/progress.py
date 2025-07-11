from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class BatchContext:
    """Represents the context for a batch of work."""

    batch_id: str
    total_items: int
    processed_items: int = 0
    status: str = "pending"
    stats: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """
    Tracks progress for workflows, especially for batch processing tasks.
    """

    def __init__(self):
        self._batches: Dict[str, BatchContext] = {}

    def track_batch(self, batch_id: str, total_files: int) -> BatchContext:
        """
        Starts tracking a new batch of files.
        """
        if batch_id not in self._batches:
            context = BatchContext(batch_id=batch_id, total_items=total_files)
            self._batches[batch_id] = context
        return self._batches[batch_id]

    def update_progress(self, batch_id: str, processed: int, status: str):
        """
        Updates the progress of a batch.
        """
        if batch_id in self._batches:
            self._batches[batch_id].processed_items = processed
            self._batches[batch_id].status = status

    def get_statistics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Aggregates and returns statistics for a given workflow.

        Note: The link between workflow_id and batch_id is not yet defined.
        This is a placeholder implementation.
        """
        # This is a mock implementation. In a real scenario, we would
        # aggregate stats from all batches related to the workflow_id.

        total_files = sum(b.total_items for b in self._batches.values())
        processed_files = sum(b.processed_items for b in self._batches.values())

        return {
            "file_processing": {
                "total_files": total_files,
                "processed": processed_files,
                "errors": 0,  # Placeholder
            },
            "by_source_type": [],  # Placeholder
        }
