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
# ------------------------------
board_w_mm         = 100
board_l_mm         = 100
substract_h_mm     = 1.27
TL_w_mm            = 1.07
metallization_t_mm = 0.035
# LUT dimensions
# ------------------------------
tube_inner_diam_mm = 1.0
tube_outer_diam_mm = 1.6
# Simulation frequencies (GHz)
# ------------------------------
freq_min = 0.5
freq_max = 3.5
# Initial structure parameters
# ------------------------------
# SC1 — detuned parallel slots (low-frequency supercell) 
SC1_DIMS = {
    "slot1_length": 90.0,       # L1 (mm) — reference λ/2 slot
    "slot2_length": 70.0,       # L2 (mm) — detuned slot
    "slot_width":    0.20,      # gs (mm) — same for both slots (fixed, not optimised)
    "separation":    6.00,      # centre-to-centre Y distance (mm)
    "offset_x":      7.00,      # X offset of slot 2 from slot 1 (mm)
}
SC1_POS = {"x": 0, "y": -30}    # centre of slot 1

# SC2 — T-loaded slot (high-frequency supercell) 
SC2_DIMS = {
    "arm_length":    22.0,      # L_main (mm) — horizontal λ/2 arm
    "arm_width":      0.20,     # gs_arm (mm) — fixed, not optimised
    "stem_length":   11.4,      # L_branch (mm) — vertical λ/4 stem
    "stem_width":     0.20,     # gs_stem (mm) — fixed, not optimised
    "stem_x_offset":  0.05,     # mm from arm centre (0 = EIT-like)
    "stem_dir":       1,        # +1 → stem grows toward +Y (fixed)
}
SC2_POS = {"x": 0, "y": 0}      # centre of horizontal arm


# ==================================================================
#                         Workflow
# ==================================================================
# ==================================================================
# STEP 1 — Create static model
# ==================================================================
print("=" * 50)
print("STEP 1 — Create static model")
print("=" * 50)

print("Defining materials...")
define_materials(model=model)
print("Done.")

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
# Step 3 — Create and simulate initial structure
# ==================================================================
print("=" * 50)
print("STEP 3 — Create and simulate initial structure")
print("=" * 50)

print("Building initial sensor structure...")
build_initial_structure(
    model=model,
    metallization_t_mm=metallization_t_mm,
    board_w_mm=board_w_mm,
    board_l_mm=board_l_mm,
    resonator_type_1="low_frequency_supercell",
    dims_1=SC1_DIMS,
    position_1=SC1_POS,
    name_1="SC1",
    resonator_type_2="high_frequency_supercell",
    dims_2=SC2_DIMS,
    position_2=SC2_POS,
    name_2="SC2",
    tube_inner_diam_mm=tube_inner_diam_mm,
    tube_outer_diam_mm=tube_outer_diam_mm
)
print("Done.")

print("Simulating initial structure...")
run_and_save_initial(mws_prj, simulation, OUTPUT_DIR, "initial_structure")
print("Done.")

# ==================================================================
# Step 4 — Optimize structure using Simulated Annealing
# ==================================================================

