"""
calculation_engine.py

This module defines the CalculationEngine class, which executes analytics calculations
based on instructions provided in YAML configuration files.
"""

import polars as pl
import yaml

class CalculationEngine:
    """
    A class to execute analytics calculations based on YAML configurations.

    Attributes:
        yaml_file (str): Path to the YAML configuration file.
        parsed_yaml (dict): Parsed YAML content.
        exec_namespace (dict): Namespace for executing code snippets.
    """

    def __init__(self, yaml_file):
        """
        Initialize the CalculationEngine with a YAML configuration file.

        Args:
            yaml_file (str): Path to the YAML configuration file.
        """
        self.yaml_file = yaml_file
        self.parsed_yaml = None
        self.exec_namespace = {'pl': pl}
        self.load_yaml()  # Ensure YAML is loaded during initialization

    def load_yaml(self):
        """
        Load and parse the YAML configuration file.
        """
        with open(self.yaml_file, 'r') as file:
            self.parsed_yaml = yaml.safe_load(file)

    def execute_steps(self, data_namespace):
        """
        Execute the steps defined in the YAML configuration.

        Args:
            data_namespace (dict): Namespace containing data variables.

        Returns:
            Any: The result of the analytics calculation.
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
                code = step['python']
                exec(code, self.exec_namespace)
            # Execute code in 'polars' section if present
            if 'polars' in step:
                code = step['polars']
                exec(code, self.exec_namespace)
        # Return the result from exec_namespace
        return self.exec_namespace.get('result')

    def _resolve_includes(self, steps):
        """
        Recursively resolve includes in the steps.

        Args:
            steps (list): List of steps from the YAML.

        Returns:
            list: Resolved list of steps.
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
                included_steps = self._resolve_includes(included_steps)
                resolved_steps.extend(included_steps)
            else:
                resolved_steps.append(step)
        return resolved_steps

