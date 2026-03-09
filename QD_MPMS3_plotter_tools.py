import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

class MPMSDataset:
    """
    Base class to handle reading and storing MPMS3 .dat files.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = {}
        self.data = pd.DataFrame()
        self._load_data()

    def _load_data(self):
        """
        Private method to parse the MPMS3 file.
        It should read line by line to extract the header into self.metadata,
        find the '[Data]' line, and load the rest into self.data using pandas.
        """
        with open(self.filepath, "r", encoding="utf-8-sig", errors="replace") as file:
            lines = file.readlines()

        data_line_index = None
        for index, line in enumerate(lines):
            if line.strip() == "[Data]":
                data_line_index = index
                break

        if data_line_index is None:
            raise ValueError("Invalid MPMS3 file: '[Data]' section not found.")

        self.metadata = {}
        for line in lines[:data_line_index]:
            stripped_line = line.strip()

            if not stripped_line or stripped_line.startswith(";"):
                continue
            if stripped_line in {"[Header]", "[Data]"}:
                continue

            parts = [part.strip() for part in stripped_line.split(",")]
            key = parts[0]
            values = parts[1:]

            if not values:
                parsed_value = None
            elif len(values) == 1:
                parsed_value = values[0]
            else:
                parsed_value = values

            if key in self.metadata:
                if not isinstance(self.metadata[key], list):
                    self.metadata[key] = [self.metadata[key]]
                self.metadata[key].append(parsed_value)
            else:
                self.metadata[key] = parsed_value

        data_block = "".join(lines[data_line_index + 1:]).strip()
        if not data_block:
            self.data = pd.DataFrame()
            return

        self.data = pd.read_csv(StringIO(data_block), na_values=[""], skip_blank_lines=True)
        self.data.columns = [column.strip() for column in self.data.columns]

    def get_column(self, column_name):
        """Helper to safely retrieve a column from the dataframe."""
        if column_name in self.data.columns:
            return self.data[column_name]
        else:
            raise KeyError(f"Column '{column_name}' not found in dataset.")


class MTMeasurement(MPMSDataset):
    """
    Subclass for Moment vs. Temperature measurements (e.g., ZFC/FC).
    """
    def plot_m_vs_t(self, ax=None, title="Moment vs Temperature"):
        """Plots Moment against Temperature."""
        if ax is None:
            fig, ax = plt.subplots()
        
        # MPMS3 headers usually look like 'Temperature (K)' and 'Moment (emu)'
        temperature = self.get_column('Temperature (K)')
        moment = self.get_column('Moment (emu)')
        
        ax.plot(temperature, moment, marker='o', linestyle='-', markersize=4)
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Moment (emu)")
        ax.set_title(title)
        ax.grid(True)
        
        return ax

    def calculate_susceptibility(self, applied_field):
        """Calculates X = M / H."""
        # TODO: Implement susceptibility calculation
        pass


class MHMeasurement(MPMSDataset):
    """
    Subclass for Moment vs. Magnetic Field measurements (e.g., Hysteresis loops).
    """
    def plot_m_vs_h(self, ax=None, title="Hysteresis Loop"):
        """Plots Moment against Magnetic Field."""
        if ax is None:
            fig, ax = plt.subplots()
            
        field = self.get_column('Magnetic Field (Oe)')
        moment = self.get_column('Moment (emu)')
        
        ax.plot(field, moment, marker='o', linestyle='-', markersize=4)
        ax.set_xlabel("Magnetic Field (Oe)")
        ax.set_ylabel("Moment (emu)")
        ax.set_title(title)
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.grid(True)
        
        return ax


class DualMHMeasurement:
    """
    Subclass to handle two MH datasets, one at low Temperature and one at high Temperature, for direct comparison.
    
    The constructor should take two file paths, load both datasets, and store them as attributes.
    The plot_m_vs_h method should be overridden to plot both datasets on the same axes with different colors and a legend.
    """
    def __init__(self, filepath1, filepath2):
        self.dataset1 = MHMeasurement(filepath1)
        self.dataset2 = MHMeasurement(filepath2)

    def plot_m_vs_h(self, ax=None, title="Hysteresis Loop Comparison"):
        """Plots both MH datasets on the same axes for comparison."""
        if ax is None:
            fig, ax = plt.subplots()
        
        # Plot first dataset
        field1 = np.array(self.dataset1.get_column('Magnetic Field (Oe)'))
        moment1 = np.array(self.dataset1.get_column('Moment (emu)'))
        # Label with temperature from metadata if available, otherwise use generic labels
        temp1 = np.round(np.mean(self.dataset1.get_column('Temperature (K)')), 1) if 'Temperature (K)' in self.dataset1.data.columns else 'Unknown Temp'
        
        
        # Plot second dataset
        field2 = np.array(self.dataset2.get_column('Magnetic Field (Oe)'))
        moment2 = np.array(self.dataset2.get_column('Moment (emu)'))
        temp2 = np.round(np.mean(self.dataset2.get_column('Temperature (K)')), 1) if 'Temperature (K)' in self.dataset2.data.columns else 'Unknown Temp'
        

        # If 

        # Plot both datasets with different colors and a legend
        ax.plot(field1, moment1, marker='o', linestyle='-', markersize=4, label=f'Dataset 1 ({temp1} K)')
        ax.plot(field2, moment2, marker='o', linestyle='-', markersize=4, label=f'Dataset 2 ({temp2} K)')
        
        ax.set_xlabel("Magnetic Field (Oe)")
        ax.set_ylabel("Moment (emu)")
        ax.set_title(title)
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.grid(True)
        ax.legend()
        
        return ax