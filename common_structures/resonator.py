# ==================================================================
# RESONATOR DEFINITIONS
# All resonators are carved into the GND plane via boolean subtract.
# z extents are always fixed to the metallization thickness.
# ==================================================================


def half_wavelength(model, dims, position, name, metallization_t_mm):
    """
    Carves a half-wavelength rectangular slot resonator into the GND plane.

    Parameters
    ----------
    model : Model
        The Model instance (from model.py).
    dims : dict
        Resonator dimensions:
            "length"  : float  — total slot length along X (mm)
            "width"   : float  — slot width along Y (mm)
    position : dict
        Center position of the resonator:
            "x"  : float  — X center (mm)
            "y"  : float  — Y center (mm)
    name : str
        Unique name for the resonator solid.
    metallization_t_mm : float
        GND plane thickness (mm). Defines the Z carving depth.

    Expected dims keys: "length", "width"
    """
    half_l = dims["length"] / 2
    half_w = dims["width"]  / 2
    cx     = position["x"]
    cy     = position["y"]

    model.geometry.brick(
        name=name,
        component="sensor",
        material="Vacuum",
        x_min=cx - half_l, x_max=cx + half_l,
        y_min=cy - half_w, y_max=cy + half_w,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", name)


def dumbell(model, dims, position, name, metallization_t_mm):
    """
    Carves a dumbbell slot resonator into the GND plane.
    The shape consists of two square end-pads connected by a thin slot.

    Parameters
    ----------
    model : Model
        The Model instance (from model.py).
    dims : dict
        Resonator dimensions:
            "total_length"  : float  — total length from outer pad edge to outer pad edge (mm)
            "slot_width"    : float  — width of the connecting slot (mm)
            "pad_size"      : float  — side length of the square end pads (mm)
    position : dict
        Center position of the resonator:
            "x"  : float  — X center (mm)
            "y"  : float  — Y center (mm)
    name : str
        Unique name prefix for the resonator solids (3 bricks are created).
    metallization_t_mm : float
        GND plane thickness (mm). Defines the Z carving depth.

    Expected dims keys: "total_length", "slot_width", "pad_size"

    Geometry layout (top view):
        [ pad_left ] --- slot --- [ pad_right ]
                      ^ slot_width tall
    """
    total_l  = dims["total_length"]
    slot_w   = dims["slot_width"]
    pad_size = dims["pad_size"]
    cx       = position["x"]
    cy       = position["y"]

    half_pad  = pad_size / 2
    half_slot = slot_w  / 2

    # total_length spans from bottom of lower pad to top of upper pad
    half_total = total_l / 2
    pad_inner  = half_total - pad_size   # inner edge of each pad (toward center)

    # --- Top pad ---
    model.geometry.brick(
        name=f"{name}_pad_top",
        component="sensor",
        material="Vacuum",
        x_min=cx + pad_inner, x_max=cx + half_total,
        y_min=cy - half_pad,  y_max=cy + half_pad,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_pad_top")

    # --- Bottom pad ---
    model.geometry.brick(
        name=f"{name}_pad_bot",
        component="sensor",
        material="Vacuum",
        x_min=cx - half_total, x_max=cx - pad_inner,
        y_min=cy - half_pad,   y_max=cy + half_pad,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_pad_bot")

    # --- Connecting slot ---
    model.geometry.brick(
        name=f"{name}_slot",
        component="sensor",
        material="Vacuum",
        x_min=cx - pad_inner, x_max=cx + pad_inner,
        y_min=cy - half_slot, y_max=cy + half_slot,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_slot")


def low_frequency_supercell(model, dims, position, name, metallization_t_mm):
    """
    Detuned parallel-slot pair supercell (SC1 — low-frequency).

    Two nearly-identical transverse half-wavelength slots are carved into the GND
    plane, separated along the feedline direction (Y) and slightly detuned in
    length.  Their hybridised even/odd supermodes produce a Fano/EIT-like feature
    between the two split resonances.

    Geometry (top view — GND plane, feedline along Y, board width along X)
    -----------------------------------------------------------------------

           ┌─────────────── slot 1 (L1) ───────────────┐   ← centre at position
           └───────────────────────────────────────────┘

              ┌─────────────── slot 2 (L2) ───────────────┐  ← centre at
              └───────────────────────────────────────────┘     (pos.x + offset_x,
                                                                  pos.y − separation)

    Ground-truth mapping (history.txt VBA variables)
    ------------------------------------------------
        lslot1  → dims["slot1_length"]
        gs1     → dims["slot_width"]
        lslot2  → dims["slot2_length"]   (L2 = L1 * (1 + delta), delta ≈ 0.005–0.025)
        gs2     → dims["slot_width"]     (same width for both slots)
        D       → encoded in position["y"]   (slot 1 Y centre in board coords)
        L       → dims["separation"]         (centre-to-centre Y distance)
        S       → dims["offset_x"]           (X offset of slot 2 from slot 1)

    Parameters
    ----------
    model : Model
        The Model instance (from model.py).
    dims : dict
        "slot1_length" : float
            Slot 1 total length along X (mm).  Reference half-wave resonator.
        "slot2_length" : float
            Slot 2 total length along X (mm).  Typically slot1_length * (1 + delta)
            where delta ∈ [0.005, 0.025] places the design in the Fano regime.
        "slot_width" : float
            Gap width of both slots along Y (mm).  Typical value: 0.2 mm.
        "separation" : float
            Centre-to-centre Y distance between slot 1 and slot 2 (mm).
            Edge-to-edge gap s = separation − slot_width.
            Fano regime on RO3010 50-mil: s ≈ 1–6 mm → separation ≈ 1.2–6.2 mm.
        "offset_x" : float
            X offset of slot 2 centre from slot 1 centre (mm).
            Zero → purely vertical arrangement (symmetric coupling).
            Non-zero → additional horizontal asymmetry (optional Fano tuning knob).
    position : dict
        Centre of slot 1 (the reference slot): {"x": float, "y": float}.
        Slot 2 is placed at (position["x"] + offset_x, position["y"] − separation).
    name : str
        Prefix for all solid names.  Two solids are created: "{name}_slot1",
        "{name}_slot2".
    metallization_t_mm : float
        GND plane thickness (mm).  Defines the Z carving depth.
    """
    L1  = dims["slot1_length"]
    L2  = dims["slot2_length"]
    gs  = dims["slot_width"]
    sep = dims["separation"]
    S   = dims["offset_x"]
    cx  = position["x"]
    cy  = position["y"]

    # --- Slot 1: reference slot, centred at (cx, cy) ---
    model.geometry.brick(
        name=f"{name}_slot1",
        component="sensor",
        material="Vacuum",
        x_min=cx - L1 / 2, x_max=cx + L1 / 2,
        y_min=cy - gs  / 2, y_max=cy + gs  / 2,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_slot1")

    # --- Slot 2: detuned, vertically offset by −separation, horizontally by +S ---
    cx2 = cx + S
    cy2 = cy - sep
    model.geometry.brick(
        name=f"{name}_slot2",
        component="sensor",
        material="Vacuum",
        x_min=cx2 - L2 / 2, x_max=cx2 + L2 / 2,
        y_min=cy2 - gs  / 2, y_max=cy2 + gs  / 2,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_slot2")


def high_frequency_supercell(model, dims, position, name, metallization_t_mm):
    """
    T-loaded slot supercell (SC2 — high-frequency).

    A transverse half-wavelength main slot (bright mode) carved into the GND plane
    is loaded by a perpendicular quarter-wavelength branch slot (dark mode).
    The junction position 'junction_p' controls the bright↔dark coupling strength
    and therefore the Fano/EIT lineshape asymmetry (Pozar ch. 8).

    Geometry (top view — GND plane)
    --------------------------------

                  ╔═══════════════════ arm (L_arm) ══════════════════╗
                  ╚══════════════════════════════════════════════════╝

                            │ stem (L_stem, stem_dir = +1)
                            │
        junction_p = 0.5  →  stem at arm centre   → EIT-like  (q → ∞)
        junction_p = 0.35 →  stem off-centre       → Fano      (q finite)
        junction_p = 0.20 →  stem near arm end     → weak coupling

    Ground-truth mapping (history.txt VBA variables)
    ------------------------------------------------
        lslot3          → dims["arm_length"]
        gs3             → dims["arm_width"]
        lslot4          → dims["stem_length"]
        gs4             → dims["stem_width"]
        p (hist)        → stem_x_offset / arm_length
          (stem X centre from arm centre = stem_x_offset [mm]
           ≡ p_hist * lslot3  with  p_hist = stem_x_offset / arm_length)
        gc (hist)       → derived from dims["arm_width"] and dims["stem_dir"]
          (gc = cy + arm_width/2  when stem_dir = +1, i.e. stem goes upward)
          (gc = cy − arm_width/2 − stem_length  when stem_dir = −1)

    Parameters
    ----------
    model : Model
        The Model instance (from model.py).
    dims : dict
        "arm_length" : float
            Total length of the horizontal main slot along X (mm).
            This is the half-wave bright-mode resonator.
        "arm_width" : float
            Gap width of the main slot along Y (mm).  Typical value: 0.2 mm.
        "stem_length" : float
            Length of the vertical branch slot along Y (mm).
            This is the quarter-wave dark-mode resonator.
        "stem_width" : float
            Gap width of the vertical branch slot along X (mm).
            Typical value: 0.2 mm (same as arm_width for symmetry).
        "stem_x_offset" : float
            X offset of the stem centre from the arm centre (mm).
              0.0  → stem at arm centre               → EIT-like (recommended start)
              ±small (e.g. ±0.05–2 mm) → off-centre  → Fano (start ~0.05 mm)
              ±arm_length/2            → stem at arm tip → very weak coupling
            Positive values shift the stem toward +X; negative toward −X.
            The stem X centre in board coordinates:
              stem_cx = position["x"] + stem_x_offset
        "stem_dir" : int
            Direction the stem extends from the arm.
              +1 → stem grows in +Y direction (upward in board plane)
              −1 → stem grows in −Y direction (downward in board plane)
            The stem is contiguous with the arm at the junction edge.
    position : dict
        Centre of the horizontal arm: {"x": float, "y": float}.
    name : str
        Prefix for all solid names.  Two solids are created: "{name}_arm",
        "{name}_stem".
    metallization_t_mm : float
        GND plane thickness (mm).  Defines the Z carving depth.
    """
    L_arm   = dims["arm_length"]
    gs_arm  = dims["arm_width"]
    L_stem  = dims["stem_length"]
    gs_stem = dims["stem_width"]
    x_off   = dims["stem_x_offset"]   # mm from arm centre; 0 = EIT-like
    d       = int(dims["stem_dir"])    # +1 or −1
    cx      = position["x"]
    cy      = position["y"]

    # X centre of the stem. x_off = 0 → EIT-like; x_off ≠ 0 → Fano asymmetry.
    stem_cx = cx + x_off

    # Y extents of the stem — contiguous with the arm at the junction edge.
    if d >= 0:                           # stem extends upward (+Y)
        stem_ymin = cy + gs_arm / 2
        stem_ymax = cy + gs_arm / 2 + L_stem
    else:                                # stem extends downward (−Y)
        stem_ymin = cy - gs_arm / 2 - L_stem
        stem_ymax = cy - gs_arm / 2

    # --- Horizontal arm ---
    model.geometry.brick(
        name=f"{name}_arm",
        component="sensor",
        material="Vacuum",
        x_min=cx - L_arm / 2,   x_max=cx + L_arm / 2,
        y_min=cy - gs_arm / 2,  y_max=cy + gs_arm / 2,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_arm")

    # --- Vertical stem (overlapping the arm at the junction is intentional —
    #     both regions are Vacuum so CST takes the union correctly) ---
    model.geometry.brick(
        name=f"{name}_stem",
        component="sensor",
        material="Vacuum",
        x_min=stem_cx - gs_stem / 2, x_max=stem_cx + gs_stem / 2,
        y_min=stem_ymin,              y_max=stem_ymax,
        z_min=-metallization_t_mm, z_max=0
    )
    model.boolean.subtract("sensor", "GND", "sensor", f"{name}_stem")


def create_cell(model, resonator_type, dims, position, name, metallization_t_mm):
    """
    Selector function: creates the specified resonator type at the given position.

    Parameters
    ----------
    model : Model
        The Model instance (from model.py).
    resonator_type : str
        Type of resonator to create. Options:
            "half_wavelength"          — rectangular slot resonator
            "dumbell"                  — dumbbell (dog-bone) slot resonator
            "low_frequency_supercell"  — SC1: detuned parallel-slot pair
            "high_frequency_supercell" — SC2: T-loaded slot resonator
    dims : dict
        Dimension dictionary passed to the selected resonator function.
        See half_wavelength(), dumbell(), create_low_frequency_supercell(), or
        create_high_frequency_supercell() for required keys.
    position : dict
        Reference position: {"x": float, "y": float}.
        Meaning depends on resonator type — see individual docstrings.
    name : str
        Unique name (or prefix) for the resonator solid(s).
    metallization_t_mm : float
        GND plane thickness in mm.

    Raises
    ------
    ValueError
        If resonator_type is not recognised.
    """
    if resonator_type == "half_wavelength":
        half_wavelength(model, dims, position, name, metallization_t_mm)
    elif resonator_type == "dumbell":
        dumbell(model, dims, position, name, metallization_t_mm)
    elif resonator_type == "low_frequency_supercell":
        low_frequency_supercell(model, dims, position, name, metallization_t_mm)
    elif resonator_type == "high_frequency_supercell":
        high_frequency_supercell(model, dims, position, name, metallization_t_mm)
    else:
        raise ValueError(
            f"Unknown resonator type '{resonator_type}'. "
            "Available types: 'half_wavelength', 'dumbell', "
            "'low_frequency_supercell', 'high_frequency_supercell'."
        )