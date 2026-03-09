This is a Python notebook that is able to:
* Load in Quantum Design MPMS 3 data files
* Plot Moment versus Temperature plots (with background flattening)
* Plot Moment versus H-field. For thin-film samples on diamagnetic substrates it is important to be able to substract this diamagnetic contribution to the signal.
* Perform subtraction of MH loops at different temperatures. For example Hematite below T_M should have no reorientable moment within the ab-plane. Above $T_M$ we know it has a reorientable moment due to the DMI interaction. Performing a subtraction of the MH-loops above and below T_M gives a MH-loop that is directly resulting from the canted moment and not impurities within the subtrate etc.

I include example data files for a Hematite thin-film on a Al2O3 substrate (Moment vs Temperature, Moment vs H-field at 200K and 340K) and an Al2O3 substrate (Moment vs H-field at 200K and 340K) to demonstrate the capabilities.
