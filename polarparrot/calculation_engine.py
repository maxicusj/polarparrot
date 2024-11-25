"""
This module defines the CalculationEngine class, which executes analytics calculations
based on instructions provided in YAML configuration files.

The CalculationEngine is designed to handle configurations that may include Python 
and Polars code snippets, as well as nested includes from other YAML files.

Use Cases:
- Automated data transformations.
- Customizable analytics workflows.

Limitations:
- YAML files must conform to a specific structure.
- Assumes Polars and Python code snippets are correctly formatted.

Example:
    engine = CalculationEngine('config.yaml')
    data = {'df': pl.DataFrame(...)}
    result = engine.execute_steps(data)
"""

import polars as pl
import yaml


class CalculationEngine:
    """
    A class to execute analytics calculations based on YAML configurations.

    The CalculationEngine is particularly suited for tasks that involve:
    - Data manipulations using Polars DataFrames.
    - Custom analytics workflows written in Python or Polars.
    """

    def __init__(self, yaml_file):
        """
        Initialize the CalculationEngine with a YAML configuration file.

        Args:
            yaml_file (str): Path to the YAML configuration file.

        Note:
            Automatically loads and parses the YAML file during initialization.

        Attributes:
            yaml_file (str): Path to the provided YAML configuration file.
            parsed_yaml (dict): Parsed content of the YAML configuration file.
            exec_namespace (dict): Namespace for executing code snippets, initialized
                                   with Polars (imported as `pl`).
        """
        self.yaml_file = yaml_file
        self.parsed_yaml = None
        self.exec_namespace = {'pl': pl}
        self.load_yaml()  # Ensure YAML is loaded during initialization

    def load_yaml(self):
        """
        Load and parse the YAML configuration file.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            yaml.YAMLError: If the YAML file cannot be parsed.
        """
        with open(self.yaml_file, 'r') as file:
            self.parsed_yaml = yaml.safe_load(file)

    def execute_steps(self, data_namespace):
        """
        Execute the steps defined in the YAML configuration.

        Args:
            data_namespace (dict): Namespace containing data variables to be used 
                                   during code execution.

        Returns:
            Any: The result of the analytics calculation, typically stored in the 
                 `result` key of `exec_namespace`.

        Note:
            The YAML file must define a structure with a 'task' key containing a 
            list of 'steps'. Each step can include 'python' or 'polars' code snippets.
        """
        # Merge data_namespace into exec_namespace
        self.exec_namespace.update(data_namespace)
        steps = self.parsed_yaml['task']['steps']

        # Handle includes
        steps = self._resolve_includes(steps)

        for step in steps:
            print(f"Executing Step: {step['step']}")
            # Execute code in 'python' section if present
            if 'python' in step:
                exec(step['python'], self.exec_namespace)
            # Execute code in 'polars' section if present
            if 'polars' in step:
                exec(step['polars'], self.exec_namespace)

        # Return the result from exec_namespace
        return self.exec_namespace.get('result')

    def _resolve_includes(self, steps):
        """
        Recursively resolve includes in the steps.

        Args:
            steps (list): List of steps from the YAML.

        Returns:
            list: Resolved list of steps.

        Note:
            Includes are resolved recursively, and steps are merged in the order 
            they are encountered. Conflicts or duplicate steps are not handled explicitly.
        """
        resolved_steps = []
        for step in steps:
            if 'include' in step:
                include_file = step['include']
                # Load included YAML file
                with open(include_file, 'r') as file:
                    included_yaml = yaml.safe_load(file)
                included_steps = included_yaml['task']['steps']
                # Recursively resolve includes
                resolved_steps.extend(self._resolve_includes(included_steps))
            else:
                resolved_steps.append(step)
        return resolved_steps