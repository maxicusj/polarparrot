# Analytics Calculation Engine

This project provides a modular analytics calculation engine that allows you to plug in different YAML configurations to compute various analytics using Polars DataFrames.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Running the Metrics Runner](#running-the-metrics-runner)
  - [Generating Documentation](#generating-documentation)
  - [Running Regression Tests](#running-regression-tests)
- [Project Structure](#project-structure)
- [Customization](#customization)
- [License](#license)

## Overview

The analytics calculation engine is designed to process data based on instructions provided in YAML configuration files. It uses Polars for data manipulation and supports Sphinx for documentation generation.

## Features

- Modular design with separation of data, configuration, and computation.
- Supports dynamic analytics calculations via YAML configurations.
- Includes regression testing capabilities using YAML configurations.
- Sphinx documentation for codebase.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Packages listed in `requirements.txt`

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/analytics-calculation-engine.git
   cd analytics-calculation-engine

