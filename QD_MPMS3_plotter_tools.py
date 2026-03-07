import pandas as pd
import matplotlib.pyplot as plt

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
        # TODO: Implement MPMS3 specific parsing logic here
        pass

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