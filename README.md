# **Portfolio Analytics Calculation Engine**

This project provides a modular YAML based portfolio analytics calculation engine. This engine allows to plug in  YAML configurations to compute various portfolio related analytics. Engine adheres to YAML schema and is utilising Polars or Python instructions. This project also hosts a dash app that relies on a local LLM model to create schema compliant YAML files. These YAML files are consumed and interpreted by the calculation engine provided. 

[![Build Package](https://github.com/maxicusj/polarparrot/actions/workflows/python-package.yml/badge.svg)](https://github.com/maxicusj/polarparrot/actions/workflows/python-package.yml)

[![CodeQL Advanced](https://github.com/maxicusj/polarparrot/actions/workflows/codeql.yml/badge.svg)](https://github.com/maxicusj/polarparrot/actions/workflows/codeql.yml)

[![Release Package to PyPi](https://github.com/maxicusj/polarparrot/actions/workflows/publish.yml/badge.svg)](https://github.com/maxicusj/polarparrot/actions/workflows/publish.yml)

---

## **Table of Contents**

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Running Analytics defined in JSON config file](#Running-Analytics-defined-in-JSON-config-file)
  - [unning Regression Tests](#Running-Regression-Tests)
  - [Running Unit Tests](#Running-Unit-Tests)
  - [Running Analytics via CURL Command](#Running-Analytics-via-CURL-Command)
  - [Running Analytics via Web UI](#Running-Analytics-via-Web-UI)
  - [Generating YAML config Files with GPT Assistant](#Generating-YAML-config-Files-with-GPT-Assistant)
- [Project Structure](#project-structure)
- [Customization](#customization)
- [License](#license)

---

## **Overview**

The analytics calculation engine is designed to process data based on instructions provided in YAML configuration files. It leverages **Polars** for data manipulation and supports **Sphinx** for documentation generation.


### **System Context**

```mermaid
graph TD
    A[User] -->|Interacts with| B[Dash Web UI]
    B -->|Sends JSON data| C[Backend Service]
    C -->|Fetches data from| G[Data Service]
    G -->|Fetches data from| D[SQL Server]
    C -->|Processes YAML files with| E[Calculation Engine]
    E -->|Uses| F[Polars]
    E -->|Uses| I[YAML Files]
    C -->|Interacts with| H[GPT App]
    H -->|Generates| I[YAML Files]
    C -->|Returns results to| B
    B -->|Displays results to| A
```

### **Video Demo**
<p style="text-align: center;">
  <a href="https://www.youtube.com/watch?v=Ni_uL8xlDas">
    <img src="https://img.youtube.com/vi/Ni_uL8xlDas/0.jpg" alt="IMAGE ALT TEXT HERE" />
  </a>
</p>


---

## **Features**

- Modular design with separation of data, configuration, and computation.
- Dynamic analytics calculations via YAML configurations.
- Regression testing capabilities with YAML support.
- Sphinx documentation for the codebase.

---

## **Getting Started**

### **Prerequisites**

- SQL Server database (e.g., SQL Server Docker container) to simulate database access. One can use docker image, e.g. https://github.com/chriseaton/docker-adventureworks, https://hub.docker.com/r/chriseaton/adventureworks
- Python 3.11 or higher.
- For GPT app to work, local installation of ollama with some LLM models is needed. See https://ollama.com
- Packages listed in `requirements.txt`.

---

### **Installation**

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/maxicusj/polarparrot.git
   cd polarparrot
   ```

2. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Environment Configuration (.env)**  
   Create a `.env` file in the root directory with the following content:
   ```plaintext
   DB_SERVER=localhost
   DB_DATABASE=AdventureWorks
   DB_USERNAME=sa
   DB_PASSWORD=password
   ```

4. **Start Backend Services, Web UI and GPT Assistant**  
   Start the services with the provided script:
   ```bash
   ./start_services.sh
   ```

---

## **Usage**

### **Running Analytics defined in JSON config file**
Run the selected YAML metrics against mockup test data:
```bash
python metrics_runner.py analytics_list.json
```

### **Running Regression Tests**
Run regression on YAML metrics against mockup test data in data.py:
```bash
python tests/regression_runner.py
```

### **Running Unit Tests**
Run the selected YAML metrics against mockup test data:
```bash
python tests/unit_tests_runner.py
```

### **Running Analytics via CURL Command**  
   You can test the backend service with a sample request:
   ```bash
   curl -X POST http://localhost:8088/analytics \
   -H "Content-Type: application/json" \
   -d '{
     "positions_json": "[{\"instrument_id\": 1, \"weight_1\": 0.00005, \"weight_2\": 0.00004, \"weight_3\": 0.00003, \"weight_4\": 0.00005, \"is_laggard\": true}, {\"instrument_id\": 2, \"weight_1\": 0.00007, \"weight_2\": 0.00006, \"weight_3\": 0.00007, \"weight_4\": 0.00006, \"is_laggard\": false}, {\"instrument_id\": 3, \"weight_1\": 0.0001, \"weight_2\": 0.00008, \"weight_3\": 0.00002, \"weight_4\": 0.0001, \"is_laggard\": true}, {\"instrument_id\": 4, \"weight_1\": 0.00002, \"weight_2\": 0.00005, \"weight_3\": 0.00009, \"weight_4\": 0.00002, \"is_laggard\": true}, {\"instrument_id\": 5, \"weight_1\": 0.00009, \"weight_2\": 0.00007, \"weight_3\": 0.00005, \"weight_4\": 0.00007, \"is_laggard\": false}]", 
     "analytics_list_json": "{\"analytics\": [\"yaml/0002.yaml\", \"yaml/0004.yaml\"]}"
   }'
   ```

   ### **Running Analytics via Web UI** 
   ```
   http://localhost:8050
   ```

   ### **Generating YAML config Files with GPT Assistant** 
   ```
   http://localhost:8080
   ```


---

## **Project Structure**

- **`metrics_runner.py`**: Executes analytics calculations as per YAML configurations.
- **`regression_runner.py`**: Validates metrics using regression tests.
- **`unit_tests_runner.py`**: Validates metrics using regression tests.
- **`start_services.sh`**: Starts backend services and the web UI.
- **`requirements.txt`**: Lists required Python packages.
- **`.env`**: Environment variables for database connection.

- **`calculation_engine.py`**: The actual analytics engine.
- **`backend_service.py`**: Backend service.
- **`data_service.py`**: Data service, providing interface to the SQL database.
- **`app.py`**: Web UI for running analytics against provided YAML config and portfolio positions.
- **`gpt/gpt_service.py`**: Web UI for generating YAMLs with the help of an LLM.
- **`data/data.sql`**: Sample SQL table and data population script for instrument_categorization table. Used by analytics engine.

---

## **Customization**

You can customize this engine by:
- Adding new YAML files to the `yaml/` directory to define analytics configurations.
- Generating new YAML files by talking to a locally available LLM model(http://localhost:8080) and placing the genrated files to the `yaml/` directory to be interrpreted by the engine.
- Extending the Polars DataFrame manipulation logic in the `calculaton_engine.py` file.

---

## **License**

This project is licensed under [MIT License](LICENSE).

---
