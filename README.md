# AeroDrift

**Agentic Cloud Topology & Remediation Graph**

AeroDrift is a beginner-friendly prototype for **Agentic Cloud Topology & Remediation Graph** analysis. It simulates AWS resources locally, builds a directed NetworkX topology, detects a risky Internet-to-Database route, recommends remediation, displays a Rich terminal dashboard, and stores each scan in SQLite.

## Project Overview

The prototype models a small cloud environment:

`Internet -> Public Security Group -> Web Server -> Application Server -> Database`

The route is intentionally unsafe for demonstration purposes. AeroDrift reports the security drift and provides practical next steps without requiring an AWS account or credentials.

## Features

- Mock AWS resource and relationship collection
- Directed cloud topology graph using NetworkX
- Internet-to-Database reachability detection
- Colored Rich CLI dashboard
- Remediation recommendations
- SQLite scan history
- Modular, readable Python files suitable for an internship demonstration

## Project Architecture

AeroDrift is organized as a small, function-based pipeline. Each module owns a
single responsibility, which keeps the project easy to explain, test, and
extend.

```text
main.py
  |
  +--> aws_data.py --> graph_engine.py --> drift_detector.py --> remediation.py
  |                                                                    |
  +---------------------------------------------------+----------------+
                                                      |
                                      +---------------+---------------+
                                      v                               v
                              dashboard.py                    database.py
                              Rich terminal UI                 SQLite history
```

### Module Responsibilities

- **`main.py`** starts the application and coordinates the complete scan from data loading through persistence.
- **`aws_data.py`** defines the `CloudResource` model, supplies validated mock resources, and provides directed relationships.
- **`graph_engine.py`** converts resources and relationships into a NetworkX `DiGraph` with node attributes and edge labels.
- **`drift_detector.py`** checks whether a directed path exists from the public `internet` node to the `database` node.
- **`remediation.py`** converts the drift finding into ordered, practical security recommendations.
- **`dashboard.py`** renders node counts, edge counts, drift status, and recommendations with Rich.
- **`database.py`** creates the local SQLite table and stores each scan's UTC timestamp, status, and recommendations.

`main.py` owns orchestration, while the other modules perform focused work and
return data to the next stage. This separation makes it possible to replace
the mock data source, dashboard, or storage layer independently in the future.

The intentionally exposed demonstration route is:

`Internet -> Public Security Group -> Web Server -> Application Server -> Database`

This makes the security finding reproducible while keeping the prototype independent of AWS accounts, credentials, and network access.

## Workflow

When `python main.py` runs, data moves through the application in this order:

1. `main.py` calls `load_mock_resources()` to load five simulated cloud resources.
2. `build_topology()` adds those resources as graph nodes and adds their directed relationships as edges.
3. `detect_security_drift()` uses NetworkX reachability to check the Internet-to-Database path.
4. `generate_recommendations()` selects remediation guidance based on the finding.
5. `display_dashboard()` presents node count, edge count, drift status, and recommendations.
6. `save_scan_result()` writes the UTC scan time, status, and combined recommendations to SQLite.

The workflow is deterministic by design: every demonstration run starts with the same mock topology and should produce the same drift finding.

## Technologies Used

- Python 3.10+
- NetworkX
- Rich
- SQLite (Python standard library)

## Installation and Setup

Requirements: Python 3.10 or newer. No AWS account, credentials, or cloud configuration is needed.

Clone the repository and enter the project directory:

```bash
git clone https://github.com/<your-username>/AeroDrift.git
cd AeroDrift
```

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
python -c "import networkx, rich; print('AeroDrift dependencies are ready')"
```

## Project Structure

```text
AeroDrift/
├── main.py                 # Application entry point and scan coordinator
├── aws_data.py             # Mock resources, relationships, and validation
├── graph_engine.py         # NetworkX directed topology construction
├── drift_detector.py       # Internet-to-Database reachability check
├── remediation.py          # Security remediation recommendation logic
├── database.py             # SQLite schema setup and scan persistence
├── dashboard.py             # Rich CLI dashboard rendering
├── requirements.txt        # Runtime Python dependencies
├── README.md               # Project documentation and demonstration guide
├── .gitignore              # Ignores environments, caches, and local secrets
├── data/                   # Runtime data directory
│   └── scan_results.db     # Generated SQLite scan history
└── screenshots/            # Optional screenshots for project presentation
	└── .gitkeep            # Keeps the empty directory in Git
```

`data/scan_results.db` is created automatically when the first scan runs. Python cache directories and the virtual environment are intentionally excluded from version control.

## Usage Examples

### Run a topology scan

From the project root, after activating the virtual environment:

```bash
python main.py
```

The command loads mock resources, builds the topology, checks reachability, displays the dashboard, and saves the result. Each run appends one scan result to `data/scan_results.db`.

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

If you see `ModuleNotFoundError` for `networkx` or `rich`, activate the project virtual environment and install the requirements again:

```bash
python -m pip install -r requirements.txt
```

If the error continues, confirm that `python` and `pip` point to the same environment:

```bash
python -m pip --version
python -c "import networkx, rich; print('Dependencies imported successfully')"
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
git remote add origin https://github.com/<your-username>/AeroDrift.git
git push -u origin main
```

If the remote URL is incorrect, update it with:

```bash
git remote set-url origin https://github.com/<your-username>/AeroDrift.git
```

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

### 1. What is AeroDrift?

AeroDrift is a local Python prototype that models cloud resources as a directed graph, detects an unsafe Internet-to-Database path, and generates remediation recommendations.

### 2. Does AeroDrift connect to AWS?

No. The current version uses mock AWS data only and does not require an AWS account, credentials, or network access.

### 3. What security problem does the demo detect?

It detects whether a directed path exists from the public `internet` node to the `database` node. That path represents a potentially unsafe public route to the data layer.

### 4. Which resources are included in the mock topology?

The topology contains an Internet entry point, a public security group, a web server, an application server, and a database.

### 5. Why does the demo always report drift?

The mock relationship data intentionally includes the route `Internet -> Public Security Group -> Web Server -> Application Server -> Database`, making the security finding reproducible for demonstrations.

### 6. What does NetworkX do in the project?

NetworkX stores the cloud resources as nodes and their communication relationships as directed edges. AeroDrift uses NetworkX reachability to check the Internet-to-Database path.

### 7. What recommendations does AeroDrift generate?

For the demonstrated drift, it recommends closing unrestricted security-group access, restricting public access to trusted sources, and removing the unnecessary Internet-to-Database route.

### 8. Where are scan results saved?

Scan results are stored in `data/scan_results.db`, a SQLite database created automatically when the application runs for the first time.

### 9. Does every scan overwrite the previous result?

No. Each successful run appends a new record containing the UTC scan time, status, and combined recommendations.

### 10. How do I run AeroDrift?

Activate the virtual environment, install the dependencies, and run `python main.py` from the project root. See [Installation and Setup](#installation-and-setup) for the full process.

### 11. Can I change the simulated cloud resources?

Yes. Update the resource definitions and relationship tuples in `aws_data.py`. Keep resource IDs consistent with relationship endpoints so graph validation succeeds.

### 12. Can AeroDrift automatically fix cloud security issues?

No. The current version only detects drift and provides recommendations. It does not modify cloud resources, and its mock-data-only design makes it safe to run locally.

### 13. Can I use AeroDrift without Rich or NetworkX?

No. Rich provides the terminal dashboard and NetworkX provides graph construction and reachability analysis. Install both through `requirements.txt`.

### 14. Is the project suitable for learning or an internship demonstration?

Yes. Its modular pipeline shows resource modeling, graph analysis, security detection, recommendation generation, CLI presentation, and database persistence in a small runnable project.

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

## Upload To GitHub

1. Create a new empty repository on GitHub named `AeroDrift`.
2. From this project directory, initialize Git and create the first commit:

```bash
git init
git add .
git commit -m "Build AeroDrift cloud topology prototype"
```

3. Connect the GitHub repository and push:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/AeroDrift.git
git push -u origin main
```

Do not commit cloud credentials, local environment files, or secrets. This prototype intentionally uses mock data only.