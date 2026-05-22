def set_up_boundaries(simulation):
    simulation.boundaries.define_boundaries()

def set_up_mesh(simulation):
    mesh = simulation.mesh

    # Mesh top-level settings
    mesh.set_mesh_type("PBA")
    mesh.set_creator("High Frequency")

    # MeshSettings: general / wavelength & geometry refinement
    settings = mesh.settings()
    settings.set_mesh_type("Hex")
    settings.set("Version", "1%")
    # MAX CELL - WAVELENGTH REFINEMENT
    settings.set("StepsPerWaveNear", "65")
    settings.set("StepsPerWaveFar", "30")
    settings.set("WavelengthRefinementSameAsNear", "0")
    # MAX CELL - GEOMETRY REFINEMENT
    settings.set("StepsPerBoxNear", "65")
    settings.set("StepsPerBoxFar", "30")
    settings.set("MaxStepNear", "0")
    settings.set("MaxStepFar", "0")
    settings.set("ModelBoxDescrNear", "maxedge")
    settings.set("ModelBoxDescrFar", "maxedge")
    settings.set("UseMaxStepAbsolute", "0")
    settings.set("GeometryRefinementSameAsNear", "0")
    # MIN CELL
    settings.set("UseRatioLimitGeometry", "1")
    settings.set("RatioLimitGeometry", "50")
    settings.set("MinStepGeometryX", "0")
    settings.set("MinStepGeometryY", "0")
    settings.set("MinStepGeometryZ", "0")
    settings.set("UseSameMinStepGeometryXYZ", "1")

    # Plane merge version
    settings.set_plane_merge_version("2")

    # Face / edge / ellipse refinement
    settings.set_mesh_type("Hex")
    settings.set("FaceRefinementType", "NONE")
    settings.set("FaceRefinementRatio", "2")
    settings.set("FaceRefinementStep", "0")
    settings.set("FaceRefinementNSteps", "2")
    settings.set("EllipseRefinementType", "NONE")
    settings.set("EllipseRefinementRatio", "2")
    settings.set("EllipseRefinementStep", "0")
    settings.set("EllipseRefinementNSteps", "2")
    settings.set("FaceRefinementBufferLines", "3")
    settings.set("EdgeRefinementType", "RATIO")
    settings.set("EdgeRefinementRatio", "4")
    settings.set("EdgeRefinementStep", "0")
    settings.set("EdgeRefinementBufferLines", "3")
    settings.set("RefineEdgeMaterialGlobal", "0")
    settings.set("RefineAxialEdgeGlobal", "0")
    settings.set("BufferLinesNear", "3")
    settings.set("UseDielectrics", "1")
    settings.set("EquilibrateOn", "1")
    settings.set("Equilibrate", "1.5")
    settings.set("IgnoreThinPanelMaterial", "0")

    # Snap settings
    settings.set_mesh_type("Hex")
    settings.set("SnapToAxialEdges", "0")
    settings.set("SnapToPlanes", "1")
    settings.set("SnapToSpheres", "1")
    settings.set("SnapToEllipses", "0")
    settings.set("SnapToCylinders", "1")
    settings.set("SnapToCylinderCenters", "1")
    settings.set("SnapToEllipseCenters", "1")
    settings.set("SnapToTori", "1")
    settings.set_snap_xyz("1", "1", "1")

    # Final mesh toggles and versions
    mesh.connectivity_check(True)
    mesh.use_pec_edge_model(True)
    mesh.point_acc_enhancement("0")
    mesh.set_versions(tst_version="0", pba_version="2024102825")
    mesh.set_cad_processing_method("MultiThread22", "-1")
    mesh.set_gpu_for_matrix_calculation_disabled(False)

def set_up_solver(simulation, freq_min, freq_max):
    """Configure the time-domain solver for the simulation.

    Applies the requested solver parallelization, distributed computing,
    and time-domain method settings via the Simulation.solver.time_domain
    helper.
    """
    solver = simulation.solver
    td_solver = solver.time_domain

    solver.set_frequency_range(freq_min=freq_min, freq_max=freq_max)

    td_solver.configure_parallelization(
        use_parallelization=True,
        maximum_number_of_threads=1024,
        maximum_number_of_cpu_devices=2,
        remote_calculation=False,
        use_distributed_computing=False,
        max_number_of_distributed_computing_ports=64,
        distribute_matrix_calculation=True,
        mpi_parallelization=False,
        automatic_mpi=False,
        consider_only_0d_1d_results_for_mpi=False,
        hardware_acceleration=True,
        maximum_number_of_gpus=1,
    )

    td_solver.configure_distributed_computing_parameters(
        use_distributed_computing_for_parameters=False,
        max_number_of_distributed_computing_parameters=2,
        use_distributed_computing_memory_setting=False,
        min_distributed_computing_memory_limit=0,
        use_distributed_computing_shared_directory=False,
        only_consider_0d_1d_results_for_dc=False,
    )

    td_solver.configure_time_domain_solver_method(
        method="Hexahedral",
        calculation_type="TD-S",
        stimulation_port="All",
        stimulation_mode="All",
        steady_state_limit="-40",
        mesh_adaption=False,
        auto_norm_impedance=False,
        norming_impedance="50",
        calculate_modes_only=False,
        spara_symmetry=False,
        store_td_results_in_cache=False,
        run_discretizer_only=False,
        full_deembedding=False,
        superimpose_plw_excitation=False,
        use_sensitivity_analysis=False,
    )

    solver.change_active_solver(solver_name="HF Time Domain")   