"""TestExecutor -- deterministic. The real implementation shells out to
Playwright; a recorded double stands in for tests and for this repo's own
end-to-end run (no live browser, no real Vespera backend to point it at --
see automation/README.md for why the Playwright side of this repo is kept
as reference code rather than executed in CI here)."""

from __future__ import annotations

import json
import pathlib
import subprocess

from .models import ExecutionResult


class PlaywrightTestExecutor:
    """Real implementation -- writes automation_code to disk and runs it
    through the actual Playwright test runner against a configured
    project directory. Requires a real target application; not exercised
    by this repo's own test suite."""

    def __init__(self, project_dir: str) -> None:
        self._project_dir = project_dir

    def execute(self, automation_code: str) -> list[ExecutionResult]:
        spec_path = pathlib.Path(self._project_dir) / "tests" / "generated.spec.ts"
        spec_path.write_text(automation_code)

        proc = subprocess.run(
            ["npx", "playwright", "test", str(spec_path), "--reporter=json"],
            cwd=self._project_dir, capture_output=True, text=True,
        )
        report = json.loads(proc.stdout or "{}")
        return [
            ExecutionResult(spec["title"], spec["ok"], [spec["ok"]], None if spec["ok"] else spec.get("error"))
            for spec in report.get("specs", [])
        ]


class RecordedExecutor:
    """Test double -- returns a scripted list of ExecutionResults instead
    of running a real browser. Used for the worked walkthrough and for
    testing every component upstream of TestExecutor in isolation."""

    def __init__(self, results: list[ExecutionResult]) -> None:
        self._results = results

    def execute(self, automation_code: str) -> list[ExecutionResult]:
        return self._results
