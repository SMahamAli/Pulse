"""Run Elysha's unchanged training script for an isolated synthetic research preview.

No live patient mapping, clinical threshold or replacement classifier is defined here.
The original script owns preprocessing, training and its held-out split.
"""

import hashlib
import runpy
from pathlib import Path
from threading import RLock


MODEL_SCRIPT = Path(__file__).resolve().parent.parent / "model" / "02_reassessment_model.py"


class ResearchAssessment:
    def __init__(self, script=MODEL_SCRIPT, runner=None):
        self.script = Path(script)
        self.runner = runner or runpy.run_path
        self.lock = RLock()
        self.bundle = None
        self.state = "not prepared"
        self.error = None

    def prepare(self):
        with self.lock:
            if self.bundle is not None:
                return
            self.state, self.error = "preparing", None
            try:
                namespace = self.runner(str(self.script))
                # Reuse the teammate's fitted pipeline and actual test split.
                pipeline, rows, dataset = (namespace["model"], namespace["X_test"], namespace["df"])
                if rows.empty or not hasattr(pipeline, "predict"):
                    raise ValueError("Model did not provide test inputs and a fitted predictor.")
                excluded = {
                    "patient_id",
                    "urgent_reassessment_required",
                    "reassessment_within_30_min",
                    "synthetic_data_only",
                    "label_generation_note",
                }
                if excluded.intersection(rows.columns):
                    raise ValueError("Outcome or identifier fields were included as model inputs.")
                examples = {}
                for index in rows.index:
                    identifier = str(dataset.loc[index, "patient_id"])
                    if not identifier.startswith("SYN2-") or identifier in examples:
                        raise ValueError("Expected unique synthetic research references.")
                    examples[identifier] = index
                revision = hashlib.sha256(self.script.read_bytes()).hexdigest()[:12]
                targets, predictions = namespace["y_test"], namespace["y_pred"]
                if len(predictions) != len(rows) or not targets.index.equals(rows.index):
                    raise ValueError("Evaluation outputs do not match the held-out inputs.")
                evaluation = dict(
                    testExamples=len(rows),
                    positiveExamples=int((targets == 1).sum()),
                    positiveExamplesFlagged=int(((targets == 1) & (predictions == 1)).sum()),
                    examplesFlagged=int((predictions == 1).sum()),
                )
                self.bundle = dict(
                    model=pipeline,
                    rows=rows,
                    examples=examples,
                    revision=revision,
                    evaluation=evaluation,
                )
                self.state = "ready"
            except ImportError:
                self.state = "failed"
                self.error = (
                    "AI libraries are missing. Run python -m pip install -r requirements-ai.txt."
                )
            except Exception:
                self.state = "failed"
                self.error = (
                    "The research model could not be prepared. Check the team script and dataset."
                )

    def status(self):
        return dict(
            state=self.state,
            error=self.error,
            revision=self.bundle["revision"] if self.bundle else None,
            evaluation=self.bundle["evaluation"] if self.bundle else None,
        )

    def examples(self):
        if not self.bundle:
            return []
        return list(self.bundle["examples"])[:20]

    def predict(self, identifier):
        with self.lock:
            if not self.bundle:
                raise ValueError("Prepare the research model before requesting a prediction.")
            # Only explicitly offered held-out synthetic rows are accepted.
            if identifier not in self.examples():
                raise ValueError(
                    "Choose a listed synthetic research example, not a Pulse patient ID."
                )
            index = self.bundle["examples"][identifier]
            row = self.bundle["rows"].loc[[index]]
            try:
                label = self.bundle["model"].predict(row)[0]
                if label not in (0, 1):
                    raise ValueError("Unexpected prediction label.")
            except Exception:
                raise ValueError(
                    "The model prediction failed. No completed result is available."
                ) from None
            return dict(
                state="completed",
                datasetId=identifier,
                flagged=bool(label),
                label="Reassessment research flag" if label else "No flag from this research model",
                revision=self.bundle["revision"],
                missingInputs=[column for column in row.columns if row[column].isna().any()],
            )
