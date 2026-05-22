from cst.interface import get_current_project
from automation import *
from steps import *

# ==================================================================
#                         INITIALISE
# ==================================================================
# Commons
# ------------------------------------------------------------------
mws_prj    = get_current_project()
model      = Model(mws_prj)
simulation = Simulation(mws_prj)
# Output directory for all CSVs and plots
# ------------------------------------------------------------------
OUTPUT_DIR = r"Z:\Adri\CST_Python_results"


# ==================================================================
#                         Parameters
# ==================================================================
# Microstrip dimensions
# ------------------------------------------------------------------
board_w_mm         = 100
board_l_mm         = 100
substract_h_mm     = 1.27
TL_w_mm            = 1.07
metallization_t_mm = 0.035
# Simulation frequencies (GHz)
# ------------------------------------------------------------------
freq_min = 0.5
freq_max = 3.5


# ==================================================================
# STEP 1 — Create static model
# ==================================================================
print("=" * 50)
print("STEP 1 — Create static model")
print("=" * 50)

print("Creating static geometry...")
create_static_geometry(
    model=model,
    board_w_mm=board_w_mm,
    board_l_mm=board_l_mm,
    substract_h_mm=substract_h_mm,
    TL_w_mm=TL_w_mm,
    metallization_t_mm=metallization_t_mm
)
print("Done.")

print("Creating ports")
create_ports(model=model, simulation=simulation)
print("Done.")

# ==================================================================
# STEP 2 — Set up simulation
# ==================================================================
print("=" * 50)
print("STEP 2 — Set up simulation")
print("=" * 50)

print("Defining boundaries...")
set_up_boundaries(simulation=simulation)
print("Done.")

print("Defining mesh...")
set_up_mesh(simulation=simulation)
print("Done.")

print("Defining solver settings...")
set_up_solver(simulation=simulation, freq_min=freq_min, freq_max=freq_max)
print(f"Created {simulation.get_active_solver()} solver")
print("Done.")

# ==================================================================
# Step 3 — Create initial structure
# ==================================================================
print("=" * 50)
print("STEP 3 — Create initial structure")
print("=" * 50)