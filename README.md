# AeroDrift

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

## Architecture

AeroDrift uses a small pipeline with clear responsibilities:

```text
aws_data.py
	|
	v
graph_engine.py  -->  drift_detector.py  -->  remediation.py
	|                         |                       |
	+-------------------------+-----------------------+
							  v
					dashboard.py + database.py
```

1. `aws_data.py` supplies mock resources and directed relationships.
2. `graph_engine.py` converts that data into a NetworkX `DiGraph`.
3. `drift_detector.py` checks whether a path exists from `internet` to `database`.
4. `remediation.py` creates recommendations from the finding.
5. `dashboard.py` presents the scan in the terminal.
6. `database.py` stores the scan status, timestamp, and recommendations in SQLite.
7. `main.py` coordinates the complete workflow.

The intentionally exposed route is:

`Internet -> Public Security Group -> Web Server -> Application Server -> Database`

This makes the security finding reproducible during a demonstration while keeping the project independent of AWS credentials.

## Technologies Used

- Python 3.10+
- NetworkX
- Rich
- SQLite (Python standard library)

## Installation

From the project directory, create and activate a virtual environment:

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

## Project Structure

```text
AeroDrift/
├── main.py                 # End-to-end scan workflow
├── aws_data.py             # Mock AWS resources and relationships
├── graph_engine.py         # NetworkX topology construction
├── drift_detector.py       # Security reachability check
├── remediation.py          # Recommendation generation
├── database.py              # SQLite persistence
├── dashboard.py             # Rich terminal dashboard
├── requirements.txt
├── README.md
├── data/                    # Created automatically on first scan
│   └── scan_results.db
└── screenshots/             # Place presentation screenshots here
```

## Usage

Run the scan from the project root after activating the virtual environment:

```bash
python main.py
```

The command loads mock resources, builds the topology, checks reachability, displays the dashboard, and saves the result. Each run appends one scan result to `data/scan_results.db`.

To confirm that a result was saved, use Python's built-in SQLite support:

```bash
python -c "import sqlite3; connection = sqlite3.connect('data/scan_results.db'); print(connection.execute('SELECT scan_time, status FROM scan_results ORDER BY id DESC LIMIT 1').fetchone()); connection.close()"
```

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

## Future Enhancements

- Add alternate safe and drifted topology scenarios
- Export topology diagrams as PNG or GraphML
- Add a scan history command and filters
- Add unit tests and CI checks
- Integrate read-only AWS inventory collection behind an optional adapter
- Add a recommendation confidence score and remediation approval workflow

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

update 1: project documentation improved
update 2: added project notes.