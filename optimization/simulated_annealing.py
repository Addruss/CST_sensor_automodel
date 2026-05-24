# ==================================================================
# SIMULATED ANNEALING OPTIMIZER
# Optimizes the layout and shape of two GND-plane resonators
# (one half_wavelength, one dumbell) using the CST simulation pipeline.
#
# Dependencies: model.py, simulation.py, resonator.py
# ==================================================================

import math
import random
import copy
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass, field


# ==================================================================
# EARLY-STOP MECHANISM
# A background thread listens for the 'S' key. When pressed, it sets
# a flag that causes the SA loop to exit cleanly after the current
# iteration, then continues with the best solution found so far.
# ==================================================================

class _StopFlag:
    """Thread-safe boolean flag shared between the listener and SA loop."""
    def __init__(self):
        self._stop = False
        self._lock = threading.Lock()

    def set(self):
        with self._lock:
            self._stop = True

    def is_set(self):
        with self._lock:
            return self._stop


def _keyboard_listener(stop_flag, stop_key="s"):
    """
    Runs in a background daemon thread.
    Blocks on input(); if the user types the stop key and presses Enter,
    sets the stop flag. Works reliably inside CST's Python environment
    (which does not support raw keypress detection without pynput).
    """
    print(f"  [SA] Press '{stop_key.upper()}' + Enter at any time to stop early "
          f"and use the best solution found so far.")
    while not stop_flag.is_set():
        try:
            key = input().strip().lower()
            if key == stop_key.lower():
                stop_flag.set()
                print(
                    "\n  [SA] Stop requested — finishing current iteration "
                    "and exiting with best solution found so far...\n"
                )
                break
        except EOFError:
            # input() raises EOFError when stdin is closed (non-interactive)
            break


# ==================================================================
# PARAMETER STRUCTURE
# ==================================================================

@dataclass
class OptimParam:
    """
    Represents a single optimization variable.

    Attributes
    ----------
    name    : str   — human-readable label for logging/plotting
    min     : float — lower bound (hard constraint)
    max     : float — upper bound (hard constraint)
    current : float — value used in the current candidate solution
    optim   : float — best value found so far
    """
    name:    str
    min:     float
    max:     float
    current: float
    optim:   float = field(init=False)

    def __post_init__(self):
        if not (self.min <= self.current <= self.max):
            raise ValueError(
                f"Parameter '{self.name}': current value {self.current} "
                f"is outside bounds [{self.min}, {self.max}]."
            )
        self.optim = self.current

    def randomize(self):
        """Set current to a uniformly random value within bounds."""
        self.current = random.uniform(self.min, self.max)

    def clip(self):
        """Clip current value to bounds (safety guard after perturbation)."""
        self.current = max(self.min, min(self.max, self.current))


# ==================================================================
# PARAMETER DEFINITIONS
# ==================================================================

def build_params(board_w_mm, board_l_mm, metallization_t_mm,
                 sc1_dims_init=None, sc1_pos_init=None,
                 sc2_dims_init=None, sc2_pos_init=None):
    """
    Defines all optimization parameters for the two-supercell sensor topology.

      SC1 — detuned parallel-slot pair (low-frequency Fano)
      SC2 — T-loaded slot (high-frequency EIT/Fano)

    Initial values are taken from the *_init dicts passed by auto_model.py
    so the SA starting point is always consistent with the baseline simulation.
    Slot widths and stem direction are fixed (not optimised) — passed separately.

    Parameters optimized
    --------------------
    SC1 (low-frequency supercell):
        sc1_y            : Y centre of slot 1 (mm)
        sc1_slot1_length : slot 1 length along X (mm)
        sc1_slot2_length : slot 2 length along X (mm)
        sc1_separation   : centre-to-centre Y gap between slots (mm)
        sc1_offset_x     : X offset of slot 2 from slot 1 (mm)

    SC2 (high-frequency supercell):
        sc2_y            : Y centre of arm (mm)
        sc2_arm_length   : arm length along X (mm)
        sc2_stem_length  : stem length along Y (mm)
        sc2_stem_x_off   : X offset of stem from arm centre (mm)
    """
    half_l   = board_l_mm / 2
    max_slot = board_w_mm - 2

    _s1  = sc1_dims_init or {}
    _s1p = sc1_pos_init  or {}
    _s2  = sc2_dims_init or {}
    _s2p = sc2_pos_init  or {}

    return {
        # ----------------------------------------------------------
        # SC1 — detuned parallel slots
        # ----------------------------------------------------------
        "sc1_y": OptimParam(
            name="SC1 slot1 Y centre (mm)",
            min=-half_l + 10, max=-5,
            current=float(_s1p.get("y", -30.0))
        ),
        "sc1_slot1_length": OptimParam(
            name="SC1 slot1 length (mm)",
            min=10.0, max=max_slot,
            current=float(_s1.get("slot1_length", 30.0))
        ),
        "sc1_slot2_length": OptimParam(
            name="SC1 slot2 length (mm)",
            min=10.0, max=max_slot*0.8,
            current=float(_s1.get("slot2_length", 30.45))
        ),
        "sc1_separation": OptimParam(
            name="SC1 slot separation (mm)",
            min=0.5, max=20.0,
            current=float(_s1.get("separation", 3.2))
        ),
        "sc1_offset_x": OptimParam(
            name="SC1 slot2 X offset (mm)",
            min=-(board_w_mm / 4), max=(board_w_mm / 4),
            current=float(_s1.get("offset_x", 0.0))
        ),
        # ----------------------------------------------------------
        # SC2 — T-loaded slot
        # ----------------------------------------------------------
        "sc2_y": OptimParam(
            name="SC2 arm Y centre (mm)",
            min=0.0, max=half_l - 10,
            current=float(_s2p.get("y", 0.0))
        ),
        "sc2_arm_length": OptimParam(
            name="SC2 arm length (mm)",
            min=5.0, max=max_slot,
            current=float(_s2.get("arm_length", 19.0))
        ),
        "sc2_stem_length": OptimParam(
            name="SC2 stem length (mm)",
            min=2.0, max=board_l_mm / 4,
            current=float(_s2.get("stem_length", 9.5))
        ),
        "sc2_stem_x_off": OptimParam(
            name="SC2 stem X offset (mm)",
            min=-10.0, max=10.0,
            current=float(_s2.get("stem_x_offset", 0.0))
        ),
    }

# ==================================================================
# COST FUNCTION
# ==================================================================

def cost_function(df_db, f1, f2, k1=1.0, k2=1.0, k3=0.1, k4=0.1, k5=0.1):
    """
    Evaluates the cost function from S21 data.

    CF = k1·S21(f1) + k2·S21(f2) + k3·Σ(dS21/df)² + k4·Σ|dS21/df|

    Lower CF is better (more negative S21 drives deeper notches at f1, f2).

    Returns
    -------
    cf : float
        Total scalar cost value.
    terms : dict
        All individual raw and weighted terms for logging:
            "s21_f1"    — raw S21 at f1 (dB)
            "s21_f2"    — raw S21 at f2 (dB)
            "sum_dsq"   — raw Σ(dS21/df)²
            "sum_abs"   — raw Σ|dS21/df|
            "w_s21_f1"  — k1 · S21(f1)
            "w_s21_f2"  — k2 · S21(f2)
            "w_sum_dsq" — k3 · Σ(dS21/df)²
            "w_sum_abs" — k4 · Σ|dS21/df|
    """
    # Locate S21 column robustly
    s21_col = None
    for col in df_db.columns:
        if col.replace(",", "").replace(" ", "") in ("S21", "S2,1"):
            s21_col = col
            break
    if s21_col is None:
        raise KeyError(
            f"S21 column not found. Available columns: {list(df_db.columns)}"
        )

    freqs  = df_db.index.to_numpy(dtype=float)
    s21_db = df_db[s21_col].to_numpy(dtype=float)

    # Terms 1 & 2: S21 at target frequencies via linear interpolation
    s21_f1 = float(np.interp(f1, freqs, s21_db))
    s21_f2 = float(np.interp(f2, freqs, s21_db))

    # Terms 3 & 4: numerical derivative (central differences) over full sweep
    ds21_df = np.gradient(s21_db, freqs)
    sum_dsq = float(np.sum(ds21_df ** 2))
    sum_abs = float(np.sum(np.abs(ds21_df)))

    # Term 5: parallel combination of S21 at f1 and f2
    denominator = s21_f1 + s21_f2
    parallel    = float(s21_f1 * s21_f2 / denominator) if abs(denominator) >= 1e-10 else 0.0

    w_s21_f1   = k1 * s21_f1
    w_s21_f2   = k2 * s21_f2
    w_sum_dsq  = k3 * sum_dsq
    w_sum_abs  = k4 * sum_abs
    w_parallel = k5 * parallel

    cf = w_s21_f1 + w_s21_f2 - w_sum_dsq - w_sum_abs + w_parallel

    terms = {
        "s21_f1":    s21_f1,
        "s21_f2":    s21_f2,
        "sum_dsq":   sum_dsq,
        "sum_abs":   sum_abs,
        "parallel":  parallel,
        "w_s21_f1":  w_s21_f1,
        "w_s21_f2":  w_s21_f2,
        "w_sum_dsq": w_sum_dsq,
        "w_sum_abs": w_sum_abs,
        "w_parallel": w_parallel,
    }
    return cf, terms


# ==================================================================
# PERTURBATION
# ==================================================================

def perturb(params, step_fraction=0.1):
    """
    Generates a candidate solution by Gaussian perturbation of all parameters.
    Each step std dev = step_fraction × parameter range. Clipped to bounds.
    """
    candidate = copy.deepcopy(params)
    for p in candidate.values():
        span  = p.max - p.min
        delta = random.gauss(0, step_fraction * span)
        p.current += delta
        p.clip()
    return candidate


# ==================================================================
# PROGRESS PRINTER
# ==================================================================

def _print_progress(iteration, T, cf, best_cf, terms):
    """Prints a structured one-line progress report per iteration."""
    print(
        f"[Iter {iteration:4d} | T={T:8.3f}] "
        f"CF={cf:10.4f}  Best={best_cf:10.4f}  |  "
        f"S21(f1)={terms['s21_f1']:7.3f}dB (w={terms['w_s21_f1']:7.3f})  "
        f"S21(f2)={terms['s21_f2']:7.3f}dB (w={terms['w_s21_f2']:7.3f})  "
        f"Σ(dS21²)={terms['sum_dsq']:10.3f} (w={terms['w_sum_dsq']:8.3f})  "
        f"Σ|dS21|={terms['sum_abs']:8.3f} (w={terms['w_sum_abs']:8.3f})"
    )


# ==================================================================
# CST RUN HELPER
# ==================================================================

def _run_cst(params, model, simulation, mws_prj,
             metallization_t_mm, board_w_mm, board_l_mm,
             tube_inner_diam_mm, tube_outer_diam_mm,
             sc1_slot_width=0.2, sc2_arm_width=0.2,
             sc2_stem_width=0.2, sc2_stem_dir=1):
    """
    Applies current supercell parameter values, runs the CST solver,
    and returns the S-parameter dB DataFrame.
    
    Uses carve_sensor from builder.py to manage geometry updates.

    Fixed (non-optimised) params passed as kwargs:
        sc1_slot_width : gap width of both SC1 slots (mm)
        sc2_arm_width  : SC2 arm gap width (mm)
        sc2_stem_width : SC2 stem gap width (mm)
        sc2_stem_dir   : SC2 stem direction (+1 up / -1 down)
    """
    from common_structures import carve_sensor, delete_tubes, build_tubes

    with simulation.suppress_dialogs():

        # Carve both resonators using the builder function
        carve_sensor(
            model=model,
            metallization_t_mm=metallization_t_mm,
            board_w_mm=board_w_mm,
            board_l_mm=board_l_mm,
            resonator_type_1="low_frequency_supercell",
            dims_1={
                "slot1_length": params["sc1_slot1_length"].current,
                "slot2_length": params["sc1_slot2_length"].current,
                "slot_width":   sc1_slot_width,
                "separation":   params["sc1_separation"].current,
                "offset_x":     params["sc1_offset_x"].current,
            },
            position_1={"x": 0, "y": params["sc1_y"].current},
            name_1="res_sc1",
            resonator_type_2="high_frequency_supercell",
            dims_2={
                "arm_length":    params["sc2_arm_length"].current,
                "arm_width":     sc2_arm_width,
                "stem_length":   params["sc2_stem_length"].current,
                "stem_width":    sc2_stem_width,
                "stem_x_offset": params["sc2_stem_x_off"].current,
                "stem_dir":      sc2_stem_dir,
            },
            position_2={"x": 0, "y": params["sc2_y"].current},
            name_2="res_sc2"
        )

        delete_tubes(model) 

        build_tubes(model=model, tube_inner_radius_mm=tube_inner_diam_mm/2, tube_outer_radius_mm=tube_outer_diam_mm/2,
                    board_w_mm=board_w_mm, metallization_t_mm=metallization_t_mm,
                    SC1_y1=params["sc1_y"].current, SC1_y2=params["sc1_y"].current-params["sc1_separation"].current, SC2_y=params["sc2_y"].current) 

    simulation.run()
    cst_path = mws_prj.filename()
    return simulation.results.get_s_parameters(cst_path, magnitude="db")

# ==================================================================
# SIMULATED ANNEALING
# ==================================================================

def simulated_annealing(
    model,
    simulation,
    mws_prj,
    params,
    metallization_t_mm,
    board_w_mm,
    board_l_mm,
    tube_inner_diam_mm,
    tube_outer_diam_mm,
    # Fixed (non-optimised) parameters
    sc1_slot_width=0.2,
    sc2_arm_width=0.2,
    sc2_stem_width=0.2,
    sc2_stem_dir=1,
    # Cost function targets
    f1=2.4,
    f2=5.8,
    k1=1.0,
    k2=1.0,
    k3=0.1,
    k4=0.1,
    k5=0.1,
    # SA schedule
    T_init=1.0,       # operates on normalised scale [0, 1] — do not change
    T_min=0.001,      # stopping temperature on normalised scale
    alpha=0.95,
    iterations_per_T=10,
    step_fraction=0.1,
    # Output
    output_dir=r"Z:\Adri\CST_Python_results",
    plot_live=False,
):
    """
    Runs Simulated Annealing to minimise the cost function.

    Parameters
    ----------
    params : dict of OptimParam
        Pre-built optimization parameters (from build_params).
        Must be built before calling this function.
    sc1_slot_width : float
        Fixed width of both SC1 slots (mm) — not optimised
    sc2_arm_width : float
        Fixed width of SC2 arm (mm) — not optimised
    sc2_stem_width : float
        Fixed width of SC2 stem (mm) — not optimised
    sc2_stem_dir : int
        Fixed direction of SC2 stem (+1 or -1) — not optimised

    Returns
    -------
    best_params : dict of OptimParam
    best_cf     : float
    history     : dict  (saved to sa_history.csv)
    """

    # --- Solver check: print which solver is active before starting ---
    active_solver = simulation.get_active_solver()
    print("=" * 60)
    print(f"  Active CST solver: {active_solver}")
    print("=" * 60)
    print("SIMULATED ANNEALING — Initial evaluation")
    print("=" * 60)

    _fixed = dict(
        sc1_slot_width = float(sc1_slot_width),
        sc2_arm_width  = float(sc2_arm_width),
        sc2_stem_width = float(sc2_stem_width),
        sc2_stem_dir   = int(sc2_stem_dir),
    )
    df_db = _run_cst(params, model, simulation, mws_prj,
                     metallization_t_mm, board_w_mm, board_l_mm,
                     tube_inner_diam_mm, tube_outer_diam_mm, **_fixed)
    current_cf, current_terms = cost_function(df_db, f1, f2, k1, k2, k3, k4, k5)

    best_cf     = current_cf
    best_terms  = current_terms.copy()
    best_params = copy.deepcopy(params)
    for p in best_params.values():
        p.optim = p.current

    # --- History: CF + all cost terms (current and best-so-far) ---
    history = {"iteration": [], "cf": [], "best_cf": []}
    for term_key in current_terms:
        history[term_key]           = []
        history[f"best_{term_key}"] = []

    def _log(iteration, cf, terms):
        history["iteration"].append(iteration)
        history["cf"].append(cf)
        history["best_cf"].append(best_cf)
        for term_key, val in terms.items():
            history[term_key].append(val)
            history[f"best_{term_key}"].append(best_terms[term_key])

    _log(0, current_cf, current_terms)
    _print_progress(0, T_init, current_cf, best_cf, current_terms)
    print()

    # --- Early-stop listener ---
    stop_flag = _StopFlag()
    listener  = threading.Thread(
        target=_keyboard_listener,
        args=(stop_flag,),
        daemon=True   # dies automatically when main thread exits
    )
    listener.start()

    # --- Main SA loop ---
    T            = T_init
    iteration    = 0
    stop_reason  = "temperature"   # updated if stopped early

    while T > T_min and not stop_flag.is_set():
        for _ in range(iterations_per_T):
            iteration += 1

            # 1. Perturb
            candidate = perturb(params, step_fraction)

            # 2. Evaluate
            df_db_c = _run_cst(candidate, model, simulation, mws_prj,
                                metallization_t_mm, board_w_mm, board_l_mm,
                                tube_inner_diam_mm, tube_outer_diam_mm, **_fixed)
            candidate_cf, candidate_terms = cost_function(
                df_db_c, f1, f2, k1, k2, k3, k4, k5
            )

            # 3. Acceptance
            # delta_cf is normalised by |current_cf| so that T operates on
            # a scale of [0, 1] regardless of the absolute CF magnitude.
            # This prevents exp(-delta/T) collapsing to 0 when CF >> T.
            delta_cf = candidate_cf - current_cf
            ref      = max(abs(current_cf), 1e-9)   # avoid division by zero
            if delta_cf < 0 or random.random() < math.exp(-delta_cf / (ref * T)):
                params        = candidate
                current_cf    = candidate_cf
                current_terms = candidate_terms

                if current_cf < best_cf:
                    best_cf     = current_cf
                    best_terms  = current_terms.copy()
                    best_params = copy.deepcopy(params)
                    for key, p in best_params.items():
                        p.optim = params[key].current

            # 4. Log current state (accepted or not)
            _log(iteration, current_cf, current_terms)

            # 5. Print
            _print_progress(iteration, T, current_cf, best_cf, current_terms)

            # Early stop check (checked every iteration, not just per T block)
            if stop_flag.is_set():
                stop_reason = "user request (S key)"
                break

        # Cool down after each block of iterations_per_T
        T *= alpha

        if plot_live:
            _plot(history, output_dir, save=False, show=True)

    # --- Summary ---
    print("\n" + "=" * 60)
    if stop_reason == "temperature":
        print(f"SA COMPLETE (temperature reached T_min) — Best CF = {best_cf:.4f}")
    else:
        print(f"SA STOPPED EARLY ({stop_reason}) at iteration {iteration} — Best CF = {best_cf:.4f}")
    print("\nBest parameters:")
    for key, p in best_params.items():
        print(f"  {p.name}: {p.optim:.4f}")
    print("\nBest cost terms:")
    print(f"  S21(f1) = {best_terms['s21_f1']:8.4f} dB   weighted: {best_terms['w_s21_f1']:8.4f}")
    print(f"  S21(f2) = {best_terms['s21_f2']:8.4f} dB   weighted: {best_terms['w_s21_f2']:8.4f}")
    print(f"  Σ(dS21/df)²  = {best_terms['sum_dsq']:10.4f}   weighted: {best_terms['w_sum_dsq']:8.4f}")
    print(f"  Σ|dS21/df|   = {best_terms['sum_abs']:10.4f}   weighted: {best_terms['w_sum_abs']:8.4f}")
    print(f"  Parallel S21  = {best_terms['parallel']:10.4f}   weighted: {best_terms['w_parallel']:8.4f}")
    print("=" * 60)

    # --- Save CSV ---
    df_hist = pd.DataFrame(history)
    df_hist.to_csv(rf"{output_dir}\sa_history.csv", index=False)
    print(f"\nHistory saved to {output_dir}\\sa_history.csv")

    # --- Final plots ---
    _plot(history, output_dir, save=True, show=True)

    return best_params, best_cf, history


# ==================================================================
# PLOTTING
# ==================================================================

def _plot(history, output_dir, save=True, show=False):
    """
    Generates two figures:
      1. Cost function evolution (current and best CF vs iteration)
      2. Cost term evolution — raw and weighted, 4 subplots (one per term)
    """
    iterations = history["iteration"]

    # --- Figure 1: Total cost function ---
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(iterations, history["cf"],      label="Current CF", alpha=0.6)
    ax1.plot(iterations, history["best_cf"], label="Best CF",    linewidth=2)
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Cost Function Value")
    ax1.set_title("Cost Function Evolution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    if save:
        fig1.savefig(rf"{output_dir}\sa_cost_function.png", dpi=150)
        print(f"Plot saved: {output_dir}\\sa_cost_function.png")
    if show:
        plt.pause(0.1)
    else:
        plt.close(fig1)

    # --- Figure 2: Individual cost terms (2×2 grid) ---
    terms_meta = [
        ("s21_f1",   "w_s21_f1",   "S21(f1)",        "dB"),
        ("s21_f2",   "w_s21_f2",   "S21(f2)",        "dB"),
        ("sum_dsq",  "w_sum_dsq",  "Σ(dS21/df)²",    ""),
        ("sum_abs",  "w_sum_abs",  "Σ|dS21/df|",     ""),
        ("parallel", "w_parallel", "Parallel S21",    "dB"),
    ]

    n_terms = len(terms_meta)
    n_cols  = 2
    n_rows  = math.ceil(n_terms / n_cols)
    fig2, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4 * n_rows))
    axes = axes.flatten()

    for i, (raw_key, w_key, label, unit) in enumerate(terms_meta):
        ax = axes[i]
        ylabel = f"{label} [{unit}]" if unit else label

        # Raw term (left y-axis)
        line1, = ax.plot(iterations, history[raw_key],
                         color=f"C{i}", label="Current (raw)", alpha=0.7)
        line2, = ax.plot(iterations, history[f"best_{raw_key}"],
                         color=f"C{i}", linestyle="--", linewidth=2,
                         label="Best (raw)")
        ax.set_ylabel(ylabel, color=f"C{i}")
        ax.tick_params(axis='y', labelcolor=f"C{i}")

        # Weighted term (right y-axis)
        ax2 = ax.twinx()
        line3, = ax2.plot(iterations, history[w_key],
                          color=f"C{i+4}", label="Current (weighted)", alpha=0.7,
                          linestyle="-.")
        line4, = ax2.plot(iterations, history[f"best_{w_key}"],
                          color=f"C{i+4}", linestyle=":", linewidth=2,
                          label="Best (weighted)")
        ax2.set_ylabel("Weighted value", color=f"C{i+4}")
        ax2.tick_params(axis='y', labelcolor=f"C{i+4}")

        ax.set_xlabel("Iteration")
        ax.set_title(label)
        ax.grid(True, alpha=0.3)

        lines  = [line1, line2, line3, line4]
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, fontsize=8)

    # Hide unused subplot if odd number of terms
    for j in range(len(terms_meta), len(axes)):
        axes[j].set_visible(False)

    plt.suptitle("Cost Term Evolution (Raw vs Weighted)", fontsize=13)
    plt.tight_layout()
    if save:
        fig2.savefig(rf"{output_dir}\sa_cost_terms.png", dpi=150)
        print(f"Plot saved: {output_dir}\\sa_cost_terms.png")
    if show:
        plt.pause(0.1)
    else:
        plt.close(fig2)