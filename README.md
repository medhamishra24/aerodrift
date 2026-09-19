# AeroDrift — Agentic Cloud Topology & Remediation Graph

AeroDrift is a local Python-based CloudOps security monitoring and remediation system. It uses mock AWS resources, a directed NetworkX topology graph, security-drift detection, AST-based remediation generation and validation, controlled local remediation execution, SQLite topology history, a FastAPI web API, a web dashboard, and ReportLab incident reports.

AeroDrift is designed for demonstration and learning. It does not connect to AWS or make uncontrolled changes to real cloud resources.

---

## Project Overview

The main security scenario modeled by AeroDrift is:

```text
Internet
   ↓
Public Security Group
   ↓
Web Server
   ↓
Application Server
   ↓
Database

The mock environment intentionally contains an unsafe Internet-to-Database route so that the drift detection and remediation workflow can be demonstrated consistently.

No AWS account or credentials are required.

⸻

Key Features

* Mock AWS resource and relationship collection
* Directed cloud topology using NetworkX
* Internet-to-Database reachability detection
* Security drift and risk identification
* Affected-resource identification
* Security-group and unsafe CIDR details
* AST-generated remediation code
* AST validation using an allowlisted structure
* Controlled local/mock remediation execution
* Remediation audit lifecycle and execution status
* SQLite historical topology snapshots
* Latest/previous topology comparison
* Timestamp-based topology comparison
* Rich terminal dashboard
* FastAPI JSON API
* Browser-based CloudOps dashboard
* Automated PDF incident reports
* Local-only and mock AWS architecture

[11:01 pm, 19/09/2026] MEDHA MISHRA: Complete Workflow

Each scan follows this workflow:
[11:01 pm, 19/09/2026] MEDHA MISHRA: Mock AWS Resources
        ↓
NetworkX Topology
        ↓
Security Drift Detection
        ↓
Unsafe Path Identification
        ↓
AST Remediation Generation
        ↓
AST Safety Validation
        ↓
Controlled Local Execution
        ↓
Audit Result
        ↓
SQLite Historical Snapshot
        ↓
Topology Comparison
        ↓
FastAPI Dashboard
        ↓
PDF Incident Report
[11:01 pm, 19/09/2026] MEDHA MISHRA: The default mock data creates:
[11:01 pm, 19/09/2026] MEDHA MISHRA: Internet → Public Security Group → Web Server
→ Application Server → Database
[11:01 pm, 19/09/2026] MEDHA MISHRA: The scan stores the topology, detects the security drift, generates and validates the remediation action, executes it only against the local mock environment, records audit information, updates topology history, and generates an incident report for the detected drift.
[11:02 pm, 19/09/2026] MEDHA MISHRA: Security Drift Detection

AeroDrift checks whether the public Internet can reach the private database through the modeled topology.

Current mock result

[11:02 pm, 19/09/2026] MEDHA MISHRA: Total nodes:             5
Total edges:             4
Internet → Database:     YES
Drift status:            DRIFT DETECTED
Risk level:              HIGH
Unsafe CIDR:             0.0.0.0/0
[11:02 pm, 19/09/2026] MEDHA MISHRA: Detected route:
[11:02 pm, 19/09/2026] MEDHA MISHRA: Internet
→ Public Security Group
→ Web Server
→ Application Server
→ Database
[11:02 pm, 19/09/2026] MEDHA MISHRA: The dashboard identifies the affected resources and displays the security-group rule responsible for the unsafe route.
[11:02 pm, 19/09/2026] MEDHA MISHRA: Controlled Remediation

When drift is detected, AeroDrift creates a remediation action using validated input.

The remediation workflow:

1. Generates the remediation source programmatically.
2. Validates the generated Python code using AST checks.
3. Allows only the expected remediation structure.
4. Executes the validated action against the local mock EC2 client.
5. Records the validation and execution result.
6. Stores audit metadata such as attempt ID, timestamp, lifecycle stage, and safety decision.

The current mock demonstration uses a security-group ingress revocation action for the unsafe public rule.
[11:02 pm, 19/09/2026] MEDHA MISHRA: Validation:        VALIDATED
Execution:         COMPLETED
Safety decision:   SAFE
Final result:      SUCCESS
[11:03 pm, 19/09/2026] MEDHA MISHRA: No real AWS resource is modified.
[11:03 pm, 19/09/2026] MEDHA MISHRA: Web Dashboard

AeroDrift includes a FastAPI-powered browser dashboard for viewing the current security posture.

The dashboard provides:

* Total nodes
* Total edges
* Drift status
* Risk level
* Affected resources
* Latest scan timestamp
* Internet-to-Database exposure path
* Affected security group
* Unsafe CIDR
* Remediation recommendations
* Current topology and resource inventory
* Historical topology changes
* Controlled remediation outcome
* Generated remediation code
* Remediation audit information
* Incident report status

Dashboard API

The FastAPI layer provides:
[11:03 pm, 19/09/2026] MEDHA MISHRA: /api/scan
/api/topology
/api/history
/api/health

[11:03 pm, 19/09/2026] MEDHA MISHRA: The dashboard uses the real scan service and persisted topology data rather than hard-coded demonstration values.
[11:03 pm, 19/09/2026] MEDHA MISHRA: Historical Topology

AeroDrift stores topology snapshots in SQLite.

Each scan records:

* Snapshot ID
* UTC timestamp
* Nodes
* Directed edges

The system compares the latest snapshot with the previous snapshot and can report:
[11:03 pm, 19/09/2026] MEDHA MISHRA: NO HISTORY
NO TOPOLOGY CHANGE
CHANGES DETECTED
[11:03 pm, 19/09/2026] MEDHA MISHRA: Added and removed nodes and edges can be displayed through the CLI and web dashboard.

Timestamp-based comparison is also supported through the CLI.
[11:04 pm, 19/09/2026] MEDHA MISHRA: Incident PDF Reports

When security drift is detected, AeroDrift generates a local PDF incident report using ReportLab.

The report includes information such as:

* Report timestamp
* Affected security group
* Unsafe security rule
* Internet-to-Database path
* Generated remediation action
* AST validation result
* Controlled execution result
* Final remediation status

The generated report is a local runtime artifact and is excluded from version control.

SAFE and UNSAFE Outcomes

SAFE / NO DRIFT

When no Internet-to-Database path exists:

* The finding is marked SAFE.
* No remediation is executed.
* No incident PDF is generated.

UNSAFE / DRIFT DETECTED

When the unsafe public path exists:

* Drift is detected.
* The Internet-to-Database path is displayed.
* Affected resources are identified.
* The remediation code is generated.
* AST validation is performed.
* Controlled mock execution is performed.
* Audit information is recorded.
* An incident PDF is generated.

Technology Stack

* Python 3.10+
* NetworkX
* FastAPI
* Uvicorn
* Rich
* SQLite
* Python ast
* ReportLab
* HTML
* CSS
* JavaScript
* Mock AWS/boto3-oriented architecture

Project Architecture:

┌─────────────────────┐
                    │   Mock AWS Data     │
                    │    aws_data.py      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │  NetworkX Topology  │
                    │  graph_engine.py    │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │   Drift Detection   │
                    │ drift_detector.py   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │    Remediation      │
                    │  remediation.py     │
                    └──────────┬──────────┘
                               ↓
              ┌────────────────┴────────────────┐
              ↓                                 ↓
      ┌───────────────┐                 ┌───────────────┐
      │    SQLite     │                 │ Incident PDF  │
      │  database.py  │                 │incident_report│
      └───────────────┘                 └───────────────┘
              ↓
      ┌────────────────────┐
      │   FastAPI API      │
      │ api.py / web_app.py│
      └──────────┬─────────┘
                 ↓
      ┌────────────────────┐
      │   Web Dashboard    │
      │ HTML/CSS/JavaScript│
      └────────────────────┘

Project Structure:

AeroDrift/
│
├── main.py
├── aws_data.py
├── graph_engine.py
├── drift_detector.py
├── remediation.py
├── database.py
├── dashboard.py
├── incident_report.py
├── scan_service.py
├── api.py
├── web_app.py
│
├── templates/
│   └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
│
├── data/
│   └── scan_results.db
│
├── screenshots/
│
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore

Module Responsibilities

* aws_data.py — Defines mock cloud resources and relationships.
* graph_engine.py — Builds the directed NetworkX topology.
* drift_detector.py — Detects unsafe Internet-to-Database reachability.
* remediation.py — Generates, validates, and controls remediation execution.
* database.py — Handles SQLite scan and topology history.
* dashboard.py — Provides Rich terminal dashboard output.
* incident_report.py — Generates local PDF incident reports.
* scan_service.py — Provides reusable scan orchestration for CLI and web consumers.
* api.py — Provides the FastAPI JSON endpoints.
* web_app.py — Serves the AeroDrift web dashboard.
* dashboard.html — Dashboard structure.
* dashboard.css — Dashboard styling.
* dashboard.js — Dashboard API integration and rendering.
* main.py — CLI entry point and project workflow coordination.

Troubleshooting

Python Not Found

If Python is not recognized:
python --version
Install Python 3.10 or newer and ensure it is available on your PATH.

Module Import Errors

Activate the virtual environment and reinstall dependencies:
python -m pip install -r requirements.txt
Port 8002 Already in Use

If the dashboard reports that port 8002 is already in use, stop the existing Uvicorn process or use another local port.
Example:
python -m uvicorn web_app:app --host 127.0.0.1 --port 8003
Then open:
http://127.0.0.1:8003/dashboard
SQLite Issues

The SQLite database is created locally when the application runs.

For a fresh local demonstration, stop the application and remove the local database:
data/scan_results.db
The application will recreate the required database structure on the next run.

⸻

Future Improvements

Possible future extensions include:

* Selectable safe and drifted topology scenarios
* Topology diagram export
* GraphML export
* Scan-history filters
* Unit and integration test coverage
* Continuous integration
* Optional read-only AWS inventory adapter
* Recommendation confidence information
* Human approval workflow before remediation

⸻

Project Screenshots

Project screenshots can be stored in the screenshots/ directory for documentation and presentation.

⸻

License

This project is intended for internship, learning, demonstration, and CloudOps automation study purposes.
