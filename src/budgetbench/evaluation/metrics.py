import json
import os

class MetricsLogger:
    """
    JSONL append-only logger for benchmark metrics.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)

    def log_metrics(self, metrics: dict):
        """
        Appends a JSON line to the file.
        """
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics) + "\n")
            f.flush() # Ensure it's written to disk (D-03)
