import cst.results
import pandas as pd


# ==================================================================
# SIMULATION CLASS
# ==================================================================
class Simulation:
    def __init__(self, project):
        self.project = project
        # Subsystems
        self.port = Port(project)
        self.boundaries = Boundaries(project)
        self.mesh = Mesh(project)
        self.solver = Solver(project)

    def run(self):
        """
        Runs the currently selected solver synchronously.
        Blocks until the solver finishes. Raises RuntimeError on failure.
        Use this for scripted end-to-end runs where you need results before continuing.
        """
        self.project.model3d.run_solver()

    def run_async(self):
        """
        Starts the solver asynchronously and returns immediately.
        Use is_running() to poll for completion.
        Useful when you want to do other work while the solver runs.
        """
        self.project.model3d.start_solver()

    def is_running(self):
        """
        Returns True if the solver is currently running.
        Use with run_async() to poll for completion.
        """
        return self.project.model3d.is_solver_running()

    def abort(self):
        """
        Aborts the currently running or paused solver.
        """
        self.project.model3d.abort_solver()

    def get_active_solver(self):
        """
        Returns the name of the currently selected solver as a string.
        Examples: "T-Solver" (time domain), "F-Solver" (frequency domain).
        Useful to verify the correct solver is active before running.
        """
        return self.project.model3d.get_active_solver_name()

    def print_active_solver(self):
        """
        Prints the currently active solver name. Convenience wrapper
        around get_active_solver() for quick checks during scripting.
        """
        name = self.get_active_solver()
        print(f"  [Simulation] Active solver: {name}")
        return name

    def set_quiet_mode(self, enabled: bool):
        """
        Enables or disables quiet mode on the DesignEnvironment.
        When enabled, message boxes (such as the 'Results May Get Incompatible
        With Model' dialog) are suppressed automatically without user input.
        Note: dialogs that require mandatory user input cannot be suppressed.
        """
        self.project.design_environment.set_quiet_mode(enabled)

    def suppress_dialogs(self):
        """
        Returns a context manager that enables quiet mode on entry
        and restores the previous state on exit. Use this to wrap
        any geometry modifications that would otherwise trigger dialogs.

        Usage:
            with simulation.suppress_dialogs():
                model.geometry.delete_solid(...)
                model.geometry.brick(...)
        """
        return self.project.design_environment.quiet_mode_enabled()

    def save(self, path="", include_results=True, allow_overwrite=False):
        """
        Saves the project.
        - path: if omitted, saves to the current filename.
        - include_results: whether to include solver results in the saved file.
        - allow_overwrite: whether to allow overwriting an existing file at path.
        """
        self.project.save(
            path=path,
            include_results=include_results,
            allow_overwrite=allow_overwrite
        )


# ==================================================================
# PORT CLASS
# ==================================================================
class Port:
    def __init__(self, project):
        self.project = project

    def create_port_from_pick(
        self,
        port_number=1,
        number_of_modes=1,
        adjust_polarization=False,
        polarization_angle=0.0,
        reference_plane_distance=0,
        text_size=50,
        coordinates="Picks",
        orientation="Positive",
        port_on_bound=True,
        clip_picked_port_to_bound=False,
        x_range_add_min="0.8128*7.55",
        x_range_add_max="0.8128*7.55",
        y_range_add_min="0",
        y_range_add_max="0",
        z_range_add_min="0.8128",
        z_range_add_max="0.8128*7.55",
        shield="PEC",
        single_ended=False
    ):
        """
        Creates a waveguide port from a previously picked face.
        Requires a face to be picked beforehand using Pick.face().
        """
        adjust_polarization_str     = "True" if adjust_polarization     else "False"
        port_on_bound_str           = "True" if port_on_bound           else "False"
        clip_picked_port_to_bound_str = "True" if clip_picked_port_to_bound else "False"
        single_ended_str            = "True" if single_ended            else "False"

        history = f"""
With Port
     .Reset
     .PortNumber "{port_number}"
     .NumberOfModes "{number_of_modes}"
     .AdjustPolarization {adjust_polarization_str}
     .PolarizationAngle "{polarization_angle}"
     .ReferencePlaneDistance "{reference_plane_distance}"
     .TextSize "{text_size}"
     .Coordinates "{coordinates}"
     .Orientation "{orientation}"
     .PortOnBound "{port_on_bound_str}"
     .ClipPickedPortToBound "{clip_picked_port_to_bound_str}"
     .XrangeAdd "{x_range_add_min}", "{x_range_add_max}"
     .YrangeAdd "{y_range_add_min}", "{y_range_add_max}"
     .ZrangeAdd "{z_range_add_min}", "{z_range_add_max}"
     .Shield "{shield}"
     .SingleEnded "{single_ended_str}"
     .Create
End With
"""
        self.project.model3d.add_to_history(
            f"Python: Create Port {port_number} from Pick",
            history
        )


# ==================================================================
# Boundaries CLASS
# ==================================================================
class Boundaries:
    def __init__(self, project):
        self.project = project

    def define_boundaries(
        self,
        x_min="expanded open",
        x_max="expanded open",
        y_min="expanded open",
        y_max="expanded open",
        z_min="expanded open",
        z_max="expanded open",
        x_symmetry="none",
        y_symmetry="none",
        z_symmetry="none",
        apply_in_all_directions=True,
        open_add_space_factor=0.5
    ):
        """
        Defines the boundary conditions for the simulation domain.
        Common boundary types: "expanded open", "electric", "magnetic",
        "periodic", "conducting wall", "open".
        """
        apply_in_all_directions_str = "True" if apply_in_all_directions else "False"

        history = f"""
With Boundary
     .Xmin "{x_min}"
     .Xmax "{x_max}"
     .Ymin "{y_min}"
     .Ymax "{y_max}"
     .Zmin "{z_min}"
     .Zmax "{z_max}"
     .Xsymmetry "{x_symmetry}"
     .Ysymmetry "{y_symmetry}"
     .Zsymmetry "{z_symmetry}"
     .ApplyInAllDirections "{apply_in_all_directions_str}"
     .OpenAddSpaceFactor "{open_add_space_factor}"
End With
"""
        self.project.model3d.add_to_history(
            "Python: Define Boundaries",
            history
        )

# ==================================================================
# MESH CLASS
# ==================================================================
class Mesh:
    def __init__(self, project):
        self.project = project
    
    def _add_history(self, title: str, body: str):
        self.project.model3d.add_to_history(title, body)

    def set_mesh_type(self, mesh_type: str):
        """Set the global mesh type.

        mesh_type: e.g. "PBA", "Tetra", etc.
        """
        history = f"""
With Mesh
     .MeshType "{mesh_type}"
End With
"""
        self._add_history("Python: Mesh SetMeshType", history)

    def set_creator(self, creator: str):
        """Record the mesh creator (tool/algorithm) used for the mesh."""
        history = f"""
With Mesh
     .SetCreator "{creator}"
End With
"""
        self._add_history("Python: Mesh SetCreator", history)

    def connectivity_check(self, enabled: bool):
        """Enable or disable mesh connectivity checks.

        enabled: True to enable, False to disable.
        """
        val = "True" if enabled else "False"
        history = f"""
With Mesh
     .ConnectivityCheck "{val}"
End With
"""
        self._add_history("Python: Mesh ConnectivityCheck", history)

    def use_pec_edge_model(self, enabled: bool):
        """Toggle PEC edge model usage for the mesh."""
        val = "True" if enabled else "False"
        history = f"""
With Mesh
     .UsePecEdgeModel "{val}"
End With
"""
        self._add_history("Python: Mesh UsePecEdgeModel", history)

    def point_acc_enhancement(self, value):
        """Set point accuracy enhancement parameter.

        `value` is written verbatim into the history block.
        """
        history = f"""
With Mesh
     .PointAccEnhancement "{value}"
End With
"""
        self._add_history("Python: Mesh PointAccEnhancement", history)

    def set_versions(self, tst_version=None, pba_version=None):
        """Set optional TST/PBA version identifiers used by the mesh system.

        Pass either or both versions as strings.
        """
        lines = []
        if tst_version is not None:
            lines.append(f"     .TSTVersion \"{tst_version}\"")
        if pba_version is not None:
            lines.append(f"     .PBAVersion \"{pba_version}\"")
        if not lines:
            return
        body = "\n".join(["With Mesh"] + lines + ["End With\n"]) + "\n"
        history = body
        self._add_history("Python: Mesh Versions", history)

    def set_cad_processing_method(self, method: str, arg: str = "-1"):
        """Set CAD processing method for mesh generation.

        `method` is the processing method name; `arg` is an optional argument.
        """
        history = f"""
With Mesh
     .SetCADProcessingMethod "{method}", "{arg}"
End With
"""
        self._add_history("Python: Mesh SetCADProcessingMethod", history)

    def set_gpu_for_matrix_calculation_disabled(self, disabled: bool):
        """Enable/disable GPU usage for matrix calculation.

        `disabled` True disables GPU, False enables it.
        """
        val = "True" if disabled else "False"
        history = f"""
With Mesh
     .SetGPUForMatrixCalculationDisabled "{val}"
End With
"""
        self._add_history("Python: Mesh SetGPUForMatrixCalculationDisabled", history)
    def settings(self):
        """Return a MeshSettings helper for MeshSettings-specific entries."""
        return MeshSettings(self.project)


class MeshSettings:
    """Helper for emitting "With MeshSettings ... End With" history blocks.

    Use `set(key, *values)` for generic keys or the convenience methods
    provided below for common groups.
    """

    def __init__(self, project):
        self.project = project

    def _add_history(self, title: str, body: str):
        self.project.model3d.add_to_history(title, body)

    def set_mesh_type(self, mesh_type: str):
        """Set the MeshSettings mesh type (e.g. "Hex")."""
        history = f"""
With MeshSettings
     .SetMeshType "{mesh_type}"
End With
"""
        self._add_history("Python: MeshSettings SetMeshType", history)

    def set(self, key: str, *values):
        """Set a generic MeshSettings key to the given values."""
        vals = ", ".join([f'"{v}"' for v in values]) if values else ''
        if vals:
            history = f"""
With MeshSettings
     .Set "{key}", {vals}
End With
"""
        else:
            history = f"""
With MeshSettings
     .Set "{key}"
End With
"""
        self._add_history(f"Python: MeshSettings Set {key}", history)

    def set_plane_merge_version(self, version: str):
        """Set the plane merge version used by the mesher."""
        history = f"""
With MeshSettings
     .Set "PlaneMergeVersion", "{version}"
End With
"""
        self._add_history("Python: MeshSettings PlaneMergeVersion", history)

    def set_snap_xyz(self, x, y, z):
        """Set snap behaviour along X/Y/Z (typically 0/1 toggles)."""
        history = f"""
With MeshSettings
     .Set "SnapXYZ" , "{x}", "{y}", "{z}"
End With
"""
        self._add_history("Python: MeshSettings SnapXYZ", history)

# ==================================================================
# SOLVER CLASS
# ==================================================================
class Solver:
    def __init__(self, project):
        self.project = project
        self.time_domain = TimeDomainSolver(project)
        self.frequency_domain = FrequencyDomainSolver(project)

    def change_active_solver(self, solver_name: str):
        """Change the currently active solver to the specified one."""
        history = f'ChangeSolverType("{solver_name}")'
        self.project.model3d.add_to_history("Python: Change Solver Type", history)

    def set_frequency_range(self, freq_min, freq_max):
        """
        Sets the simulation frequency range independently of solver configuration.
        Useful to update the range without reconfiguring the full solver.

        Parameters
        ----------
        freq_min : float  — lower bound (GHz)
        freq_max : float  — upper bound (GHz)
        """
        history = f'Solver.FrequencyRange "{freq_min}", "{freq_max}"'
        self.project.model3d.add_to_history(
            f"Python: Set Frequency Range {freq_min}-{freq_max} GHz",
            history
        )

class TimeDomainSolver:
    """Helper for emitting time-domain solver history commands.

    Use the methods here to configure CST time-domain solver properties
    in a script-friendly way. Each method records the equivalent
    historical command block to the project history.
    """

    def __init__(self, project):
        self.project = project

    def _add_history(self, title: str, body: str):
        self.project.model3d.add_to_history(title, body)

    def set(self, key: str, *values):
        """Set an arbitrary Solver property.

        key: name of the solver command without the leading dot.
        values: one or more values written verbatim as quoted strings.
        """
        vals = ", ".join([f'"{v}"' for v in values]) if values else ""
        if vals:
            history = f"""
With Solver
     .{key} {vals}
End With
"""
        else:
            history = f"""
With Solver
     .{key}
End With
"""
        self._add_history(f"Python: Solver Set {key}", history)

    def configure_parallelization(
        self,
        use_parallelization: bool = True,
        maximum_number_of_threads: int = 1024,
        maximum_number_of_cpu_devices: int = 2,
        remote_calculation: bool = False,
        use_distributed_computing: bool = False,
        max_number_of_distributed_computing_ports: int = 64,
        distribute_matrix_calculation: bool = True,
        mpi_parallelization: bool = False,
        automatic_mpi: bool = False,
        consider_only_0d_1d_results_for_mpi: bool = False,
        hardware_acceleration: bool = True,
        maximum_number_of_gpus: int = 1,
    ):
        """Configure time-domain solver parallelization and hardware settings.

        This writes a single "With Solver" history block with the
        specified parallelization and hardware acceleration options.
        """
        true_false = lambda value: "True" if value else "False"
        history = f"""
With Solver
     .UseParallelization "{true_false(use_parallelization)}"
     .MaximumNumberOfThreads "{maximum_number_of_threads}"
     .MaximumNumberOfCPUDevices "{maximum_number_of_cpu_devices}"
     .RemoteCalculation "{true_false(remote_calculation)}"
     .UseDistributedComputing "{true_false(use_distributed_computing)}"
     .MaxNumberOfDistributedComputingPorts "{max_number_of_distributed_computing_ports}"
     .DistributeMatrixCalculation "{true_false(distribute_matrix_calculation)}"
     .MPIParallelization "{true_false(mpi_parallelization)}"
     .AutomaticMPI "{true_false(automatic_mpi)}"
     .ConsiderOnly0D1DResultsForMPI "{true_false(consider_only_0d_1d_results_for_mpi)}"
     .HardwareAcceleration "{true_false(hardware_acceleration)}"
     .MaximumNumberOfGPUs "{maximum_number_of_gpus}"
End With
"""
        self._add_history("Python: Solver Configure Parallelization", history)

    def configure_distributed_computing_parameters(
        self,
        use_distributed_computing_for_parameters: bool = False,
        max_number_of_distributed_computing_parameters: int = 2,
        use_distributed_computing_memory_setting: bool = False,
        min_distributed_computing_memory_limit: int = 0,
        use_distributed_computing_shared_directory: bool = False,
        only_consider_0d_1d_results_for_dc: bool = False,
    ):
        """Configure distributed computing parameters used by the time-domain solver."""
        true_false = lambda value: "True" if value else "False"
        history = f"""
UseDistributedComputingForParameters "{true_false(use_distributed_computing_for_parameters)}"
MaxNumberOfDistributedComputingParameters "{max_number_of_distributed_computing_parameters}"
UseDistributedComputingMemorySetting "{true_false(use_distributed_computing_memory_setting)}"
MinDistributedComputingMemoryLimit "{min_distributed_computing_memory_limit}"
UseDistributedComputingSharedDirectory "{true_false(use_distributed_computing_shared_directory)}"
OnlyConsider0D1DResultsForDC "{true_false(only_consider_0d_1d_results_for_dc)}"
"""
        self._add_history("Python: Solver Configure Distributed Computing Parameters", history)

    def configure_time_domain_solver_method(
        self,
        method: str = "Hexahedral",
        calculation_type: str = "TD-S",
        stimulation_port: str = "All",
        stimulation_mode: str = "All",
        steady_state_limit: str = "-40",
        mesh_adaption: bool = False,
        auto_norm_impedance: bool = False,
        norming_impedance: str = "50",
        calculate_modes_only: bool = False,
        spara_symmetry: bool = False,
        store_td_results_in_cache: bool = False,
        run_discretizer_only: bool = False,
        full_deembedding: bool = False,
        superimpose_plw_excitation: bool = False,
        use_sensitivity_analysis: bool = False,
    ):
        """Configure the time-domain solver execution mode and related options."""
        true_false = lambda value: "True" if value else "False"
        history = f"""
With Solver
     .Method "{method}"
     .CalculationType "{calculation_type}"
     .StimulationPort "{stimulation_port}"
     .StimulationMode "{stimulation_mode}"
     .SteadyStateLimit "{steady_state_limit}"
     .MeshAdaption "{true_false(mesh_adaption)}"
     .AutoNormImpedance "{true_false(auto_norm_impedance)}"
     .NormingImpedance "{norming_impedance}"
     .CalculateModesOnly "{true_false(calculate_modes_only)}"
     .SParaSymmetry "{true_false(spara_symmetry)}"
     .StoreTDResultsInCache "{true_false(store_td_results_in_cache)}"
     .RunDiscretizerOnly "{true_false(run_discretizer_only)}"
     .FullDeembedding "{true_false(full_deembedding)}"
     .SuperimposePLWExcitation "{true_false(superimpose_plw_excitation)}"
     .UseSensitivityAnalysis "{true_false(use_sensitivity_analysis)}"
End With
"""
        self._add_history("Python: Solver Configure Time Domain Method", history)

class FrequencyDomainSolver:
    def __init__(self, project):
        self.project = project

    