import unittest
import tempfile
import os
import polars as pl
import textwrap
import yaml
import sys
import os

# Add the parent directory of the current script to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calculation_engine import CalculationEngine
from polars.testing import assert_frame_equal


class TestCalculationEngine(unittest.TestCase):
    def setUp(self):
        # Create a temporary YAML file for testing
        self.temp_yaml_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        yaml_content = textwrap.dedent('''
task:
  steps:
    - step: "Load Data"
      python: |
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    - step: "Compute Sum"
      python: |
        total = df["a"].sum()
    - step: "Include Steps"
      include: "included_steps.yaml"
    - step: "Polars Operation"
      polars: |
        df = df.with_columns((df["a"] + df["b"]).alias("c"))
''')
        self.temp_yaml_file.write(yaml_content.encode('utf-8'))
        self.temp_yaml_file.close()

        # Create included YAML file
        self.included_yaml_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        included_yaml_content = textwrap.dedent('''
task:
    steps:
      - step: "Multiply"
        python: |
          product = df["a"] * df["b"]
''')
        self.included_yaml_file.write(included_yaml_content.encode('utf-8'))
        self.included_yaml_file.close()

        # Update the include path to the temporary file
        with open(self.temp_yaml_file.name, 'r') as f:
            content = f.read()
        content = content.replace("included_steps.yaml", self.included_yaml_file.name)
        with open(self.temp_yaml_file.name, 'w') as f:
            f.write(content)

        self.engine = CalculationEngine(self.temp_yaml_file.name)

    def tearDown(self):
        # Remove temporary files
        os.unlink(self.temp_yaml_file.name)
        os.unlink(self.included_yaml_file.name)

    def test_execute_steps(self):
        data_namespace = {}
        self.engine.execute_steps(data_namespace)
        exec_namespace = self.engine.exec_namespace

        # Check if 'df' is in the namespace
        self.assertIn('df', exec_namespace)
        self.assertIsInstance(exec_namespace['df'], pl.DataFrame)

        # Check if 'total' is computed correctly
        self.assertIn('total', exec_namespace)
        self.assertEqual(exec_namespace['total'], 6)

        # Check if 'product' is computed
        self.assertIn('product', exec_namespace)
        expected_product = pl.Series([4, 10, 18])
        self.assertTrue((exec_namespace['product'] == expected_product).all())

        # Check if 'c' column is added correctly in Polars operation
        self.assertIn('df', exec_namespace)
        expected_df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [5, 7, 9]})
        assert_frame_equal(exec_namespace['df'], expected_df)

if __name__ == '__main__':
    unittest.main()