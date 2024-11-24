"""
data.py

This module contains functions to generate sample data for the analytics calculation engine.
"""

import pandas as pd

def get_positions_data():
    """
    Generate sample positions DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing positions data.
    """
    positions_data = {
        'instrument_id': range(1, 11),
        'weight_1': [0.00005, 0.00007, 0.0001, 0.00002, 0.00009, 0.00003, 0.00008, 0.00006, 0.00004, 0.00011],
        'weight_2': [0.00004, 0.00006, 0.00008, 0.00005, 0.00007, 0.00001, 0.00009, 0.00006, 0.00002, 0.0001],
        'weight_3': [0.00003, 0.00007, 0.00002, 0.00009, 0.00005, 0.00004, 0.00008, 0.00006, 0.00001, 0.00012],
        'weight_4': [0.00005, 0.00006, 0.0001, 0.00002, 0.00007, 0.00003, 0.00008, 0.00006, 0.00004, 0.00009],
        'is_laggard': [True, False, True, True, False, True, False, True, False, True],
    }
    positions_df = pd.DataFrame(positions_data)
    return positions_df

def get_instrument_categorization_data():
    """
    Generate sample instrument categorization DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing instrument categorization data.
    """
    instrument_categorization_data = {
        'instrument_id': range(1, 11),
        'credit_parent_name': [
            'Parent A', 'Parent B', 'Parent A', 'Parent C', 'Parent B',
            'Parent D', 'Parent A', 'Parent C', 'Parent D', 'Parent B'
        ],
          'currency': [
            'USD', 'EUR', 'USD', 'JPY', 'EUR',
            'CHF', 'USD', 'JPY', 'CHF', 'EUR'
        ],
        'sector1': [
            ' A', ' B', ' A', ' C', ' B',
            ' D', ' A', ' C', ' D', ' B'
        ],
    }
    instrument_categorization_df = pd.DataFrame(instrument_categorization_data)
    return instrument_categorization_df


    """
    Generate sample instrument_categorization DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing instrument categorization data.
    """
    instrument_categorization_data = {
        'instrument_id': range(1, 11),
        'currency': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'USD', 'EUR', 'GBP', 'JPY', 'CHF'],
        'credit_parent_name': ['Parent1', 'Parent2', 'Parent1', 'Parent2', 'Parent1', 'Parent2', 'Parent1', 'Parent2', 'Parent1', 'Parent2']
    }
    return pd.DataFrame(instrument_categorization_data)

def get_expected_output_0001():
    """
    Generate expected output DataFrame for yaml/0001.yaml.

    Returns:
        pd.DataFrame: Expected output DataFrame for yaml/0001.yaml.
    """
    expected_output_0001_data = {
        "category": [" A", " B", " C", " D"],
        "weight_1": [0.00005, 0.00011, 0.0, 0.0],
        "weight_2": [0.00004, 0.0001, 0.0, 0.0],
        "weight_3": [0.0, 0.00012, 0.000045, 0.0],
        "weight_4": [0.00005, 0.00009, 0.0, 0.0],
        "position_count": [2, 1, 2, 1],
    }
    return pd.DataFrame(expected_output_0001_data)

def get_expected_output_0002():
    """
    Generate expected output DataFrame for yaml/0002.yaml.

    Returns:
        pd.DataFrame: Expected output DataFrame for yaml/0002.yaml.
    """
    expected_output_0002_data = {
        "category": ["Parent A", "Parent B", "Parent C", "Parent D"],
        "weight_1": [0.0001, 0.00011, 0.0, 0.0],
        "weight_2": [0.00008, 0.0001, 0.0, 0.0],
        "weight_3": [0.0, 0.00012, 0.00009, 0.0],
        "weight_4": [0.0001, 0.00009, 0.0, 0.0],
        "position_count": [2, 1, 2, 1],
    }
    return pd.DataFrame(expected_output_0002_data)

    return pd.DataFrame(expected_output_0001_data)

def get_expected_output_0004():
    """
    Generate expected output DataFrame for yaml/0004.yaml.

    Returns:
        pd.DataFrame: Expected output DataFrame for yaml/0004.yaml.
    """
    expected_output_0004_data = {
        "category": ["CHF", "EUR", "JPY", "USD"],
        "weight_1": [0.00007, 0.00027, 0.00008, 0.00023],
        "weight_2": [0.00003, 0.00023, 0.00011, 0.00021],
        "weight_3": [0.00005, 0.00024, 0.00015, 0.00013],
        "weight_4": [0.00007, 0.00022, 0.00008, 0.00023],
        "position_count": [2, 3, 2, 3],
    }
    return pd.DataFrame(expected_output_0004_data)




