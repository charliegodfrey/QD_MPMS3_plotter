import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from numpy import logical_or as _or
from numpy import logical_and as _and

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
        
        return fig, ax

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
        
        return fig, ax


class DualMHMeasurement:
    """
    Subclass to handle two MH datasets, one at low Temperature and one at high Temperature, for direct comparison.
    
    The constructor should take two file paths, load both datasets, and store them as attributes.
    The plot_m_vs_h method should be overridden to plot both datasets on the same axes with different colors and a legend.
    """
    def __init__(self, filepath1, filepath2):
        self.dataset1 = MHMeasurement(filepath1)
        self.dataset2 = MHMeasurement(filepath2)
        self.difference = None  # Placeholder for any calculated difference between the two datasets
        self.h1 = np.array(self.dataset1.get_column('Magnetic Field (Oe)'))
        self.h2 = np.array(self.dataset2.get_column('Magnetic Field (Oe)'))
        self.m1 = np.array(self.dataset1.get_column('Moment (emu)'))
        self.m2 = np.array(self.dataset2.get_column('Moment (emu)'))

    def subtract_diamagnetic_background(self, Hc=7000, max_H=15000):
        """Subtracts the diamagnetic background from both datasets.
        Hc is the approximate coercive field of the sample - we don't perform flattening using any data within
        +- Hc.
        We also only use data within +- max_H to avoid fitting to noisy data at very high fields
        """
        fitrange = np.where(_or(_and(self.h1<-Hc, self.h1>-max_H), _and(self.h1>Hc, self.h1<max_H)))

        coeffs1 = np.polyfit(self.h1[fitrange], self.m1[fitrange], 1)
        coeffs2 = np.polyfit(self.h2[fitrange], self.m2[fitrange], 1)

        background1 = np.polyval(coeffs1, self.h1)
        background2 = np.polyval(coeffs2, self.h2)
        self.m1 = self.m1 - background1
        self.m2 = self.m2 - background2

        self.difference = self.m2 - self.m1

        # Remove the slope in the difference as well
        a, b, c, d = [-max_H,-Hc,Hc,max_H]
        fitrange1 = np.where(_and(self.h1 > a, self.h1 < b))
        fitrange2 = np.where(_and(self.h1 > c, self.h1 < d))
        coeffs_diff1 = np.polyfit(self.h1[fitrange1], self.difference[fitrange1], 1)
        coeffs_diff2 = np.polyfit(self.h1[fitrange2], self.difference[fitrange2], 1)
        background_diff = np.polyval([0.5*(coeffs_diff1[0]+coeffs_diff2[0]), 0.5*(coeffs_diff1[1]+coeffs_diff2[1])], self.h1)
        self.difference = self.difference - background_diff


    def plot_m_vs_h(self, ax=None, title="Hysteresis Loop Comparison"):
        """Plots both MH datasets on the same axes for comparison."""
        if ax is None:
            fig, ax = plt.subplots()
        
        # Label with temperature from metadata if available, otherwise use generic labels
        temp1 = np.round(np.mean(self.dataset1.get_column('Temperature (K)')), 1) if 'Temperature (K)' in self.dataset1.data.columns else 'Unknown Temp'
        temp2 = np.round(np.mean(self.dataset2.get_column('Temperature (K)')), 1) if 'Temperature (K)' in self.dataset2.data.columns else 'Unknown Temp'
        

        # If 

        # Plot both datasets with different colors and a legend
        ax.plot(self.h1, self.m1, marker='o', linestyle='-', markersize=4, label=f'Dataset 1 ({temp1} K)')
        ax.plot(self.h2, self.m2, marker='o', linestyle='-', markersize=4, label=f'Dataset 2 ({temp2} K)')
        
        ax.set_xlabel("Magnetic Field (Oe)")
        ax.set_ylabel("Moment (emu)")
        ax.set_title(title)
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.grid(True)
        ax.legend()
        
        return fig, ax
    
    def plot_difference(self, ax=None, H_field_lims=None, M_limits=None, title="Difference in M-H Curves"):
        """Plots the difference between the two MH datasets."""
        if self.difference is None:
            raise ValueError("Difference not calculated. Please run subtract_diamagnetic_background() first.")
        
        if ax is None:
            fig, ax = plt.subplots()
        
        ax.plot(self.h1, self.difference, marker='o', linestyle='-', markersize=4)
        ax.set_xlabel("Magnetic Field (Oe)")
        ax.set_ylabel("Difference in Moment (emu)")
        ax.set_title(title)
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.grid(True)
        if H_field_lims is not None:
            ax.set_xlim(-H_field_lims, H_field_lims)
        if M_limits is not None:
            ax.set_ylim(-M_limits, M_limits)
        
        return fig, ax