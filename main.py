from cst.interface import get_current_project
from automation import *
from steps import *
from optimization import simulated_annealing, build_params

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
# SA
# ------------------------------
# SA scheduling parameters
SA_T_INIT           = 1.5
SA_T_MIN            = 0.001
SA_ALPHA            = 0.95
SA_ITERATIONS_PER_T = 5
SA_STEP_FRACTION    = 0.1
# Cost function weights
K1, K2, K3, K4, K5 = 10.0, 10.0, 0.000002, 0.0002, 10.0
# Cost function frequency targets (GHz)
freq_objective_1_GHz = 0.7
freq_objective_2_GHz = 1.0


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
print("=" * 50)
print("STEP 4 — Optimize structure using SA")
print("=" * 50)

print("Building optimization parameters...")
optim_params = build_params(
    board_w_mm=board_w_mm,
    board_l_mm=board_l_mm,
    metallization_t_mm=metallization_t_mm,
    sc1_dims_init=SC1_DIMS,
    sc1_pos_init=SC1_POS,
    sc2_dims_init=SC2_DIMS,
    sc2_pos_init=SC2_POS
)
print("Done.")

print("Starting Simulated Annealing optimization...")
best_params, best_cf, history = simulated_annealing(
    model=model,
    simulation=simulation,
    mws_prj=mws_prj,
    params=optim_params,
    metallization_t_mm=metallization_t_mm,
    board_w_mm=board_w_mm,
    board_l_mm=board_l_mm,
    tube_inner_diam_mm=tube_inner_diam_mm,
    tube_outer_diam_mm=tube_outer_diam_mm,
    # Fixed (non-optimised) parameters
    sc1_slot_width=SC1_DIMS["slot_width"],
    sc2_arm_width=SC2_DIMS["arm_width"],
    sc2_stem_width=SC2_DIMS["stem_width"],
    sc2_stem_dir=SC2_DIMS["stem_dir"],
    # Cost function targets
    f1=freq_objective_1_GHz,
    f2=freq_objective_2_GHz,
    k1=K1,
    k2=K2,
    k3=K3,
    k4=K4,
    k5=K5,
    T_init=SA_T_INIT,
    T_min=SA_T_MIN,
    alpha=SA_ALPHA,
    iterations_per_T=SA_ITERATIONS_PER_T,
    step_fraction=SA_STEP_FRACTION,
    output_dir=OUTPUT_DIR,
    plot_live=False
)
print("Done.")

# ==================================================================
# STEP 5 — Save optimized results and create comparison plots
# ==================================================================
print("=" * 50)
print("STEP 5 — Save optimized results")
print("=" * 50)

# Run simulation with optimized parameters
print("Running simulation with optimized parameters...")
from common_structures import carve_sensor

with simulation.suppress_dialogs():
    carve_sensor(
        model=model,
        metallization_t_mm=metallization_t_mm,
        board_w_mm=board_w_mm,
        board_l_mm=board_l_mm,
        resonator_type_1="low_frequency_supercell",
        dims_1={
            "slot1_length": best_params["sc1_slot1_length"].optim,
            "slot2_length": best_params["sc1_slot2_length"].optim,
            "slot_width": SC1_DIMS["slot_width"],
            "separation": best_params["sc1_separation"].optim,
            "offset_x": best_params["sc1_offset_x"].optim,
        },
        position_1={"x": 0, "y": best_params["sc1_y"].optim},
        name_1="res_sc1",
        resonator_type_2="high_frequency_supercell",
        dims_2={
            "arm_length": best_params["sc2_arm_length"].optim,
            "arm_width": SC2_DIMS["arm_width"],
            "stem_length": best_params["sc2_stem_length"].optim,
            "stem_width": SC2_DIMS["stem_width"],
            "stem_x_offset": best_params["sc2_stem_x_off"].optim,
            "stem_dir": SC2_DIMS["stem_dir"],
        },
        position_2={"x": 0, "y": best_params["sc2_y"].optim},
        name_2="res_sc2"
    )

    delete_tubes(model) 

    build_tubes(model=model, tube_inner_radius_mm=tube_inner_diam_mm/2, tube_outer_radius_mm=tube_outer_diam_mm/2,
                board_w_mm=board_w_mm, metallization_t_mm=metallization_t_mm,
                SC1_y1=best_params["sc1_y"].optim, SC1_y2=best_params["sc1_y"].optim-best_params["sc1_separation"].optim, SC2_y=best_params["sc2_y"].optim) 


simulation.run()
cst_path = mws_prj.filename()
df_final_db = simulation.results.get_s_parameters(cst_path, magnitude="db", AR_filter=True)
df_final_complex = simulation.results.get_s_parameters(cst_path, magnitude="complex", AR_filter=True)
print("Done.")

# Save optimized S-parameter CSVs
print("Saving optimized S-parameter data...")
df_final_db.to_csv(rf"{OUTPUT_DIR}\final_structure_db.csv")
df_final_complex.to_csv(rf"{OUTPUT_DIR}\final_structure_complex.csv")
print(f"  Saved: {OUTPUT_DIR}\\final_structure_db.csv")
print(f"  Saved: {OUTPUT_DIR}\\final_structure_complex.csv")

# Save optimized parameters to CSV
print("Saving optimized parameters...")
import pandas as pd
params_data = []
for key, param in best_params.items():
    params_data.append({
        "Parameter": param.name,
        "Key": key,
        "Optimized Value": param.optim,
        "Min": param.min,
        "Max": param.max,
    })
df_params = pd.DataFrame(params_data)
df_params.to_csv(rf"{OUTPUT_DIR}\optimized_parameters.csv", index=False)
print(f"  Saved: {OUTPUT_DIR}\\optimized_parameters.csv")
print("Done.")

# Create comparison plot of S21 responses
print("Creating S21 comparison plot...")
import matplotlib.pyplot as plt

# Load initial response
df_initial_db = pd.read_csv(rf"{OUTPUT_DIR}\initial_structure_db.csv", index_col=0)

# Extract S21 columns (handle different naming conventions)
s21_col_initial = None
s21_col_final = None
for col in df_initial_db.columns:
    if col.replace(",", "").replace(" ", "") in ("S21", "S2,1"):
        s21_col_initial = col
        break

for col in df_final_db.columns:
    if col.replace(",", "").replace(" ", "") in ("S21", "S2,1"):
        s21_col_final = col
        break

if s21_col_initial and s21_col_final:
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot S21 responses
    ax.plot(df_initial_db.index, df_initial_db[s21_col_initial], 
            label="Initial Structure", linewidth=2, alpha=0.8)
    ax.plot(df_final_db.index, df_final_db[s21_col_final], 
            label="Optimized Structure", linewidth=2, alpha=0.8)
    
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("S21 (dB)")
    ax.set_title("S21 Response Comparison: Initial vs Optimized Sensor")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(rf"{OUTPUT_DIR}\s21_comparison.png", dpi=150)
    print(f"  Plot saved: {OUTPUT_DIR}\\s21_comparison.png")
    plt.show()
else:
    print("  Warning: S21 column not found in initial or final data")

print("Done.")
print("\n" + "=" * 50)
print("ALL STEPS COMPLETED SUCCESSFULLY")
print("=" * 50)
