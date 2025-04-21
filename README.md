# UF Engineering Research Project Dataset Builder

A Python-based data collection tool for creating comprehensive datasets of undergraduate research projects at the University of Florida's College of Engineering. This tool systematically extracts, structures, and normalizes research opportunity data to enable analysis, searching, and integration with other academic systems.

## Purpose

This project aims to create a structured dataset of research opportunities to:
- Help students discover research projects matching their skills and interests
- Enable analysis of research trends across engineering departments
- Provide a machine-readable database of faculty research interests and mentorship opportunities
- Support integration with other university systems and applications

## Overview

This command-line utility offers:
- Direct scraping from UF Engineering department web pages
- Processing of locally saved HTML files 
- Structured extraction of detailed project information
- JSON output in a consistent, normalized format for data analysis

## Supported Departments

The scraper works with all UF Engineering department research pages:

You can find all available options [here](https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/)

- Base Url for all departments: 
  https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/

- Computer & Information Science and Engineering (CISE): 
  https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/computer-and-information-science-and-engineering/

- Electrical & Computer Engineering (ECE): 
  https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/electrical-and-computer-engineering/


## Installation

### Prerequisites

- Python 3.6 or higher
- Git (optional, for cloning the repository)

### Setup

1. Clone this repository (or download the ZIP file):
   ```bash
   git clone https://github.com/raidenwilliams/uf-research-labs-data.git
   cd uf-research-labs-data
   ```

2. Create and activate a virtual environment:
   ```bash
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create directories for output data:
   ```bash
   mkdir -p data/json
   ```

## Usage

### Basic Usage

To scrape a department page directly from the web:

```bash
python script.py https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/electrical-and-computer-engineering/
```

To process a local HTML file:

```bash
python script.py ./data/raw_html/ece.html
```

### Output Options

By default, the script saves output to `./data/json/{department}_projects.json`. You can specify a custom output path:

```bash
python script.py [source] --output ./custom/path/output.json
```

## JSON Data Format

The script extracts the following fields for each project (when available):

| Field | Description | Example |
|-------|-------------|---------|
| `project_title` | Title of the research project | "Machine Learning for Signal Processing" |
| `department` | Department offering the project | "electrical_and_computer_engineering" |
| `faculty_mentor` | Professor overseeing the project | "Dr. Jane Smith" |
| `ph.d._student_mentor(s)` | Graduate students mentoring undergrads | "John Doe" |
| `terms_available` | When the project is offered | "Fall 2023, Spring 2024" |
| `student_level` | Required student classification | "Junior, Senior" |
| `prerequisites` | Required courses or skills | "Programming experience, EEL3701" |
| `credit` | Credit hours offered | "Variable, 1-3 credits" |
| `stipend` | Payment information if available | "Unpaid" or "$15/hour" |
| `application_requirements` | What students need to apply | "Resume, transcript, cover letter" |
| `application_deadline` | When applications are due | "Rolling basis" |
| `website` | Related project website | "https://project-site.edu" |
| `project_description` | Detailed information about the project | "This project will explore..." |
| `contact_email` | Email address for inquiries | "professor@ufl.edu" |
| `source` | Source URL or file | "https://www.eng.ufl.edu/..." |
| `project_id` | Unique identifier for each project | "electrical_and_computer_engineering_1" |

Example JSON entry:
```json
{
  "project_title": "Trustworthy Machine Learning",
  "faculty_mentor": "Dr. Kejun Huang",
  "ph.d._student_mentor(s)": "TBD",
  "terms_available": "Fall 2022, Spring 2023, Summer 2023",
  "student_level": "Sophomore, Junior, Senior",
  "prerequisites": "Python programming or MATLAB programming, Linear Algebra",
  "credit": "Variable",
  "application_requirements": "Resume, transcript",
  "project_description": "This project aims to develop machine learning algorithms...",
  "contact_email": "example@ufl.edu",
  "department": "electrical_and_computer_engineering",
  "source": "https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/electrical-and-computer-engineering/",
  "project_id": "electrical_and_computer_engineering_1"
}
```

## Requirements.txt

Create a `requirements.txt` file with the following contents:

```
beautifulsoup4>=4.9.3
requests>=2.25.1
argparse>=1.4.0
```