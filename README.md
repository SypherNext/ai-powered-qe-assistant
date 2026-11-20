# AI-Powered QE Assistant

This is the companion code for the Sypher course **"AI for Quality
Engineering."** It's built around one fictional company, Vespera Systems,
and its ticketing platform, Vespera Helpdesk, as both halves of that
course use it: AI as a tool that helps a QE work faster (`automation/`),
and AI as a feature inside the product that itself needs testing
(`app/`). The capstone assembles the testing side into one coherent
seven-component pipeline -- a test generator, a reviewer, an automation
generator, a quality gate, an executor, a failure analyzer, and a report
builder, wired by a thin orchestrator with no judgment of its own.

**GitHub repository:** link coming soon (ai-powered-qe-assistant)

## What's in here

```
app/            Python package: the Ticket Summarizer, Knowledge Assistant,
                adversarial guardrails, Ticket Triage Agent, and the
                seven-component capstone pipeline. Real pytest suite.
automation/     Playwright TypeScript: SLA Auto-Escalation automation,
                the hardcoded-secrets scanner, and the CI guardrail wiring.
```

The two halves map onto the course's own split: `app/` is "AI as a system
under test" (the modules on testing LLM features, RAG, security, and
agents); `automation/` is "AI as a productivity tool for QE" (the modules
on generating and maintaining test automation, and the guardrails around
it).

## What this needs that's different from most companion repos here

`ANTHROPIC_API_KEY` is **optional**. Every test in `app/tests/` runs
against `RecordedProvider` -- a test double that replays a fixed response
instead of calling a model -- so the full suite runs for $0 and needs no
key at all. You only need a real key if you want to exercise
`AnthropicProvider` against the live API yourself, the same way the
course's own golden-set regression runs are meant to happen on a schedule,
not on every change.

`automation/` has no real backend to run against. Vespera Helpdesk is a
fictional target throughout the course -- unlike some other companion
repos in this collection, there's no real running app behind these
specs. The Playwright files here are real, complete, and type-check
cleanly against the real `@playwright/test` types; they document exactly
what the course's lessons build and fix, step by step. If you want to see
them actually execute, point `playwright.config.ts`'s `baseURL` (via the
`VESPERA_BASE_URL` environment variable) at your own stand-in backend that
implements the `/api/test/*` endpoints the fixtures call.

## Set up your computer

You need Git and Python 3.11 or newer for `app/`. Node.js 18 or newer is
only needed if you also want to type-check or extend `automation/`.

| Tool | Windows | macOS | Ubuntu or Debian |
| --- | --- | --- | --- |
| Git | `winget install --id Git.Git -e` | `brew install git` | `sudo apt update && sudo apt install -y git` |
| Python | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt install -y python3 python3-venv` |
| Node.js | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `sudo apt install -y nodejs npm` |

Open a new terminal and check each tool:

```bash
git --version
python3 --version    # python --version on Windows
node --version       # only needed for automation/
```

### Get the code

```bash
git clone <ai-powered-qe-assistant repository URL> ai-powered-qe-assistant
cd ai-powered-qe-assistant
```

## Run the Python side (`app/`)

```bash
cd app
python3 -m venv .venv            # Windows: python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the whole suite -- deterministic, no network calls, no API key needed:

```bash
pytest
```

Try the pipeline yourself from a Python shell, the same way the course's
capstone lesson walks through it, entirely with `RecordedProvider`:

```bash
python3 -c "
import json
from qe_assistant.llm_provider import RecordedProvider
from qe_assistant.pipeline.analyzer import HeuristicFailureAnalyzer
from qe_assistant.pipeline.automation_generator import AnthropicAutomationGenerator
from qe_assistant.pipeline.executor import RecordedExecutor
from qe_assistant.pipeline.generator import AnthropicTestGenerator
from qe_assistant.pipeline.models import ExecutionResult
from qe_assistant.pipeline.orchestrator import run_qe_pipeline
from qe_assistant.pipeline.quality_gate import LintGuardrailChecker
from qe_assistant.pipeline.report_builder import MarkdownReportBuilder
from qe_assistant.pipeline.reviewer import ChecklistTestReviewer

report = run_qe_pipeline(
    requirement='SLA Auto-Escalation: ...',
    generator=AnthropicTestGenerator(RecordedProvider(json.dumps([
        {'title': 'SLA breach escalates', 'setup': 'status Open, 60 minutes left',
         'expected_outcome': 'priority becomes Urgent'},
    ]))),
    reviewer=ChecklistTestReviewer(required_edge_cases=[]),
    automation_generator=AnthropicAutomationGenerator(RecordedProvider(
        \"import { test, expect } from '../fixtures';\n\"
        \"test('SLA breach escalates', async ({ page }) => {\n\"
        \"  await expect(page.getByTestId('priority-pill')).toHaveText('Urgent');\n\"
        \"});\n\"
    )),
    guardrail_checker=LintGuardrailChecker(),
    executor=RecordedExecutor([ExecutionResult('SLA breach escalates', True, [True])]),
    analyzer=HeuristicFailureAnalyzer(),
    report_builder=MarkdownReportBuilder(),
)
print(report.as_markdown)
"
```

If you want to exercise `AnthropicProvider` for real (optional, and this
will spend a small amount of real API credit):

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Windows PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-..."
python3 -c "
from qe_assistant.llm_provider import AnthropicProvider
from qe_assistant.ticket_summarizer import summarize_ticket
provider = AnthropicProvider()
print(summarize_ticket('Customer: my export is stuck. Agent: looking into it.', provider))
"
```

## Run the TypeScript side (`automation/`)

```bash
cd automation
npm install
```

Type-check every spec and component against the real Playwright types
(this is what this repo's own verification pass ran -- no live browser or
backend involved):

```bash
npx tsc --noEmit
```

Run the hardcoded-secrets scanner for real, against the demo fixture that
is deliberately bad and against the real specs that should be clean:

```bash
node scripts/check-no-hardcoded-secrets.js demos/flagged-example.spec.ts   # exits 1, lists the finding
node scripts/check-no-hardcoded-secrets.js tests/*.spec.ts                 # exits 0
```

If you've pointed `VESPERA_BASE_URL` at a real stand-in backend that
implements the test-only seed/cleanup/webhook-capture endpoints the
fixtures call:

```bash
npx playwright test
```

## A note on the bugs fixed here versus the lesson text

A few real bugs turned up while assembling this repo and running it for
real, and are fixed here (and in the published lessons, kept in sync):

- `AnthropicProvider.complete()` originally read `response.content[0].text`
  directly, which raises `AttributeError` whenever the API returns a
  non-text content block ahead of the text block. Fixed to join every
  text-type block instead.
- `RecordedTools`' tool methods recorded `locals().copy()` as a call's
  recorded `arguments`, which silently included `self` and the tool's own
  return value alongside the real arguments. Fixed to build an explicit
  dict of just the real arguments; see `app/qe_assistant/triage_agent.py`.
- The security guardrail's forbidden-phrase list caught `"issuing a
  refund"` but not the past-tense `"issued a refund"` -- the exact wording
  one of the course's own worked examples uses. Fixed by adding the
  past-tense form; see `app/qe_assistant/guardrails.py`.
- The capstone pipeline's component interfaces (`TestExecutor`,
  `FailureAnalyzer`, `QEReportBuilder`) are implemented here with the
  real, working list-based signatures and argument order, correcting a
  singular/plural and argument-order mismatch against the course's own
  earlier interface sketch.

None of this changes the architecture the course teaches -- the
`LLMProvider` abstraction, the seven-component pipeline boundaries, and
the `RecordedProvider`/golden-set testing discipline are all exactly as
designed.

## License

Copyright (C) 2026 SypherNext

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). You may
use, study and change it. If you share a modified version, or run one as a website or service
that other people use, you must make your full modified source code available under the same
license. See [LICENSE](LICENSE) for the full terms.
