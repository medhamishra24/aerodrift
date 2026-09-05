# AeroDrift

A local Python application for cloud topology and remediation analysis. AeroDrift
uses mock AWS resources, a directed NetworkX graph, a Rich terminal dashboard,
SQLite topology history, and ReportLab incident reports. It never connects to
AWS or changes cloud resources.

## Project Overview

The prototype models this environment:

`Internet -> Public Security Group -> Web Server -> Application Server -> Database`

The route is intentionally unsafe so the drift check has a repeatable result.
No AWS account or credentials are required.

## Features

- Mock AWS resource and relationship collection
- Directed cloud topology graph using NetworkX
- Internet-to-Database reachability detection
- AST-generated and AST-validated remediation code
- Controlled local mock remediation execution
- Historical SQLite topology snapshots and timestamp comparison
- Colored Rich CLI dashboard with drift history
- Automated PDF incident reports for detected drift
- Small modules suitable for learning and demonstration

## Complete Workflow

Each scan follows this flow:

```text
Mock resources -> NetworkX topology -> drift detection
-> AST remediation generation -> AST safety validation
-> controlled local mock execution -> SQLite historical snapshot
-> latest/previous topology diff -> Rich dashboard -> PDF incident report
```

The default mock data intentionally creates an
`Internet -> Public Security Group -> Web Server -> Application Server -> Database`
path. A scan records the constructed graph, exercises the restricted/no-drift
check, restores mock drift, validates the allowlisted remediation AST, executes
only against the local EC2 mock, and stores the scan result. A PDF is generated
only for detected drift; SAFE/no-drift findings do not execute remediation or
create an incident report.

Run the project with:

```bash
python main.py
```

## Project Architecture

AeroDrift uses a small pipeline in which each module has one responsibility:

```text
Mock resources -> Graph -> Drift Detection -> Remediation -> History -> Dashboard/PDF
  aws_data.py     graph_engine.py   drift_detector.py   remediation.py   database.py   dashboard.py/incident_report.py
```

`main.py` coordinates the complete flow.

- **`aws_data.py`** defines `CloudResource` and supplies validated mock resources and relationships.
- **`graph_engine.py`** builds a NetworkX directed graph from those resources and relationships.
- **`drift_detector.py`** checks whether a directed path exists from `internet` to `database`.
- **`remediation.py`** generates allowlisted remediation source, validates its AST, and executes it only against a local EC2 mock while recording audit status.
- **`database.py`** stores scan results and timestamped topology snapshots, retrieves and compares history, and provides safe snapshot helpers.
- **`dashboard.py`** displays graph metrics, historical changes, drift status, and recommendations with Rich.
- **`incident_report.py`** creates a local ReportLab PDF from the existing finding, topology path, and remediation audit result.

The modules keep mock data, analysis, presentation, and storage separate.

## Technologies Used

- Python 3.10+
- NetworkX
- Rich
- ReportLab
- SQLite (Python standard library)

## Installation and Setup

Requirements: Python 3.10 or newer. No AWS account, credentials, or cloud configuration is needed.

Open a terminal in the project directory.

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify the installation:

```bash
python --version
python -c "import networkx, rich, reportlab; print('AeroDrift dependencies are ready')"
```

## Project Structure

```text
AeroDrift/
├── main.py                 # Application entry point and scan coordinator
├── aws_data.py             # Mock resources, relationships, and validation
├── graph_engine.py         # NetworkX directed topology construction
├── drift_detector.py       # Internet-to-Database reachability check
├── remediation.py          # AST-safe remediation generation and mock execution
├── database.py             # SQLite schema setup and scan persistence
├── dashboard.py            # Rich CLI dashboard rendering
├── incident_report.py      # Local ReportLab PDF incident reports
├── requirements.txt        # Runtime Python dependencies
├── README.md               # Project documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                 # MIT license
├── .gitignore              # Generated files and local settings to ignore
├── data/                   # Created when the first scan runs
│   ├── scan_results.db     # Local SQLite scan and topology history
│   └── aerodrift_incident_report.pdf  # Generated drift report
└── screenshots/            # Optional presentation screenshots
    └── .gitkeep            # Keeps the directory in Git
```

`data/scan_results.db` and incident PDFs are created automatically at runtime
and ignored by Git. Python cache directories and the virtual environment are
also intentionally excluded from version control.

## Usage Examples

### Run a topology scan

From the project root, after activating the virtual environment:

```bash
python main.py
```

Each run appends one scan result and one topology snapshot to
`data/scan_results.db`, then compares the current snapshot with the previous
available snapshot.

### Compare saved snapshots by timestamp

```bash
python main.py --compare-timestamps "FIRST_TIMESTAMP" "SECOND_TIMESTAMP"
```

The command reports `NO HISTORY`, `NO TOPOLOGY CHANGE`, or the added and removed
nodes and directed edges.

### Confirm the latest saved result

Use Python's built-in SQLite support to inspect the latest scan:

```bash
python -c "import sqlite3; connection = sqlite3.connect('data/scan_results.db'); print(connection.execute('SELECT scan_time, status FROM scan_results ORDER BY id DESC LIMIT 1').fetchone()); connection.close()"
```

Expected result format:

```text
('2026-08-23T12:00:00+00:00', 'DRIFT DETECTED')
```

The timestamp will reflect the time of your scan.

## Troubleshooting

### Python Not Found

If the terminal reports that `python` is not recognized, Python may not be installed or may not be available on your `PATH`.

- Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
- On Windows, enable **Add Python to PATH** during installation.
- Close and reopen the terminal, then verify the installation:

```bash
python --version
```

On some macOS and Linux systems, use `python3` instead of `python` in the commands in this README.

### Module Import Errors

If you see `ModuleNotFoundError` for `networkx`, `rich`, or `reportlab`, activate the project virtual environment and install the requirements again:

```bash
python -m pip install -r requirements.txt
```

If the error continues, confirm that `python` and `pip` point to the same environment:

```bash
python -m pip --version
python -c "import networkx, rich, reportlab; print('Dependencies imported successfully')"
```

Run `main.py` from the project root so Python can find the local AeroDrift modules.

### SQLite Database Issues

If the application cannot create or write `data/scan_results.db`, check that:

- You are running `python main.py` from the project directory.
- The project directory is writable.
- Another process is not holding the database file open.
- The `data` path is not a file with the same name as the required directory.

AeroDrift creates the `data` directory and database table automatically. For a local demonstration, stop the application and remove `data/scan_results.db` to start with a fresh scan history; the next run recreates it.

### GitHub Push Issues

If Git reports that `origin` is missing, add the remote and try again:

```bash
git push -u origin main
```

If the remote URL is incorrect, update it in your Git client before pushing.

Confirm the remote and branch before pushing:

```bash
git remote -v
git branch --show-current
```

For authentication failures, use GitHub's supported authentication method, such as GitHub CLI or SSH. Do not place passwords, access tokens, or other secrets in the repository or command history.

### Virtual Environment Issues

If activation fails or dependencies appear to be missing, recreate the local environment.

Windows PowerShell:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If PowerShell blocks activation scripts, run this command as your normal user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Frequently Asked Questions

### Does AeroDrift connect to AWS?

No. It uses mock data only and does not require an AWS account, credentials, or network access.

### Why does the demo report drift?

The mock topology intentionally includes a directed route from `internet` to `database`, so the finding is repeatable.

### Can I change the simulated resources?

Yes. Update the resources and relationships in `aws_data.py`. Keep resource IDs consistent with relationship endpoints so validation succeeds.

### Does AeroDrift fix the detected issue?

No cloud resource is modified. AeroDrift generates and validates an allowlisted
action, then executes it only against the in-process local mock client.

### Where is scan history stored?

Each successful scan is appended to `data/scan_results.db` with its UTC
timestamp, status, recommendations, and topology snapshot. Snapshot history is
used for latest/timestamp comparison and is never sent to AWS.

## Validation Results

The final integration was checked with:

```bash
python main.py
python main.py --compare-timestamps "FIRST_TIMESTAMP" "SECOND_TIMESTAMP"
python -m py_compile main.py database.py dashboard.py remediation.py incident_report.py
```

The normal run completed with the expected mock `DRIFT DETECTED` path, saved a
five-node/four-edge topology snapshot, displayed the historical comparison,
executed remediation only through the local mock, and generated a valid PDF.
The restricted topology check remained `NO DRIFT`; no AWS credentials or calls
were used. Automated pytest discovery requires pytest to be installed
separately in the active environment.

## Project Screenshots

### Dashboard Output

[View the AeroDrift dashboard screenshot](screenshots/dashboard.output.png.jpeg)

This screenshot shows the AeroDrift security scan, its drift detection result, the remediation recommendations, and the message confirming that the result was saved to SQLite.

### GitHub Repository

[View the AeroDrift GitHub repository screenshot](screenshots/gitHub_repository.png.jpeg)

This screenshot demonstrates the project's GitHub repository and version-control history.

## Sample Output

```text
Loading mock AWS resources...
Building cloud topology graph...
Checking for security drift...

Topology Scan
Total nodes                    5
Total edges                    4
Internet -> Database path      YES
Drift status                   DRIFT DETECTED

WARNING: Security Drift Detected - Internet can reach Database

Remediation Recommendations
1. Close the open security group to public inbound traffic.
2. Restrict public access to approved IP ranges or trusted services.
3. Remove the unnecessary Internet-to-Database route.

Scan result saved to data/scan_results.db
```

## Future Improvements

- Add selectable safe and drifted topology scenarios for demonstrations.
- Export topology diagrams as PNG or GraphML.
- Add a scan-history command with date and status filters.
- Add unit tests, integration tests, and continuous integration checks.
- Integrate read-only AWS inventory collection behind an optional adapter.
- Add recommendation confidence scores and a remediation approval workflow.
- Add structured JSON output for dashboards and external integrations.

## Upload to GitHub

Create an empty repository on GitHub, then run these commands from the project directory:

```bash
git init
git add .
git commit -m "Build AeroDrift cloud topology prototype"
```

After adding the repository's remote URL in your local Git client, push the branch:

```bash
git push -u origin main
```

Do not commit cloud credentials, local environment files, or secrets. This prototype intentionally uses mock data only.