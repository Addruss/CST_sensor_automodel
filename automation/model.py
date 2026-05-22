# model.py

class Model:
    def __init__(self, project):
        self.project = project
        # Subsystems
        self.geometry = Geometry(project)
        self.material = Material(project)
        self.boolean = Boolean(project)
        self.pick = Pick(project)


# ==================================================================
# GEOMETRY CLASS
# ==================================================================
class Geometry:
    def __init__(self, project):
        self.project = project

    def brick(
        self,
        name,
        component,
        material,
        x_min, x_max,
        y_min, y_max,
        z_min, z_max
    ):
        history_list = f"""
With Brick
     .Reset
     .Name "{name}"
     .Component "{component}"
     .Material "{material}"
     .Xrange "{x_min}", "{x_max}"
     .Yrange "{y_min}", "{y_max}"
     .Zrange "{z_min}", "{z_max}"
     .Create
End With
"""
        self.project.model3d.add_to_history(
            f"Python: Create Brick {name}",
            history_list
        )

    def delete_solid(self, component_name, solid_name):
        history = f"""
Solid.Delete "{component_name}:{solid_name}"
"""
        self.project.model3d.add_to_history(
            "Python: Delete Solid",
            history
        )


# ==================================================================
# MATERIAL CLASS
# ==================================================================
class Material:
    def __init__(self, project):
        self.project = project

    def create_normal(
        self,
        name,
        epsilon,
        mu,
        kappa,
        kappa_m,
        tand,
        tand_freq,
        tand_given,
        tand_model,
        tand_m,
        tand_m_freq,
        tand_m_given,
        tand_m_model,
        rho,
        thermal_conductivity,
        colour_r,
        colour_g,
        colour_b
    ):
        """
        Generic template for 'Normal' type dielectric/substrate materials.
        Matches the Rogers RO4003C expected output structure.
        """
        tand_given_str  = "True" if tand_given  else "False"
        tand_m_given_str = "True" if tand_m_given else "False"

        history = f"""
With Material
     .Reset
     .Name "{name}"
     .Folder ""
     .FrqType "all"
     .Type "Normal"
     .SetMaterialUnit "GHz", "mm"
     .Epsilon "{epsilon}"
     .Mu "{mu}"
     .Kappa "{kappa}"
     .TanD "{tand}"
     .TanDFreq "{tand_freq}"
     .TanDGiven "{tand_given_str}"
     .TanDModel "{tand_model}"
     .KappaM "{kappa_m}"
     .TanDM "{tand_m}"
     .TanDMFreq "{tand_m_freq}"
     .TanDMGiven "{tand_m_given_str}"
     .TanDMModel "{tand_m_model}"
     .DispModelEps "None"
     .DispModelMu "None"
     .DispersiveFittingSchemeEps "General 1st"
     .DispersiveFittingSchemeMu "General 1st"
     .UseGeneralDispersionEps "False"
     .UseGeneralDispersionMu "False"
     .Rho "{rho}"
     .ThermalType "Normal"
     .ThermalConductivity "{thermal_conductivity}"
     .SetActiveMaterial "all"
     .Colour "{colour_r}", "{colour_g}", "{colour_b}"
     .Wireframe "False"
     .Transparency "0"
     .Create
End With
"""
        self.project.model3d.add_to_history(
            f"Python: Define Material {name}",
            history
        )

    def create_lossy_metal(
        self,
        name,
        mu,
        sigma,
        rho,
        thermal_conductivity,
        specific_heat,
        youngs_modulus,
        poissons_ratio,
        thermal_expansion_rate,
        colour_r,
        colour_g,
        colour_b
    ):
        """
        Template for 'Lossy metal' type materials.
        Matches the Copper (pure) expected output structure.
        Lossy metals require two FrqType blocks: 'all' and 'static'.
        """
        history = f"""
With Material
     .Reset
     .Name "{name}"
     .Folder ""
     .FrqType "all"
     .Type "Lossy metal"
     .MaterialUnit "Frequency", "GHz"
     .MaterialUnit "Geometry", "mm"
     .MaterialUnit "Time", "s"
     .MaterialUnit "Temperature", "Kelvin"
     .Mu "{mu}"
     .Sigma "{sigma}"
     .Rho "{rho}"
     .ThermalType "Normal"
     .ThermalConductivity "{thermal_conductivity}"
     .SpecificHeat "{specific_heat}", "J/K/kg"
     .MetabolicRate "0"
     .BloodFlow "0"
     .VoxelConvection "0"
     .MechanicsType "Isotropic"
     .YoungsModulus "{youngs_modulus}"
     .PoissonsRatio "{poissons_ratio}"
     .ThermalExpansionRate "{thermal_expansion_rate}"
     .ReferenceCoordSystem "Global"
     .CoordSystemType "Cartesian"
     .NLAnisotropy "False"
     .NLAStackingFactor "1"
     .NLADirectionX "1"
     .NLADirectionY "0"
     .NLADirectionZ "0"
     .FrqType "static"
     .Type "Normal"
     .SetMaterialUnit "Hz", "mm"
     .Epsilon "1"
     .Mu "{mu}"
     .Kappa "{sigma}"
     .TanD "0.0"
     .TanDFreq "0.0"
     .TanDGiven "False"
     .TanDModel "ConstTanD"
     .KappaM "0"
     .TanDM "0.0"
     .TanDMFreq "0.0"
     .TanDMGiven "False"
     .TanDMModel "ConstTanD"
     .DispModelEps "None"
     .DispModelMu "None"
     .DispersiveFittingSchemeEps "Nth Order"
     .DispersiveFittingSchemeMu "Nth Order"
     .UseGeneralDispersionEps "False"
     .UseGeneralDispersionMu "False"
     .Colour "{colour_r}", "{colour_g}", "{colour_b}"
     .Wireframe "False"
     .Reflection "False"
     .Allowoutline "True"
     .Transparentoutline "False"
     .Transparency "0"
     .Create
End With
"""
        self.project.model3d.add_to_history(
            f"Python: Define Material {name}",
            history
        )

    def rogers_ro4003c(self):
        self.create_normal(
            name="Rogers RO4003C (lossy)",
            epsilon=3.55,
            mu=1.0,
            kappa=0.0,
            kappa_m=0.0,
            tand=0.0027,
            tand_freq=10.0,
            tand_given=True,
            tand_model="ConstTanD",
            tand_m=0.0,
            tand_m_freq=0.0,
            tand_m_given=False,
            tand_m_model="ConstKappa",      # Rogers uses ConstKappa, not ConstTanD
            rho=0.0,
            thermal_conductivity=0.71,
            colour_r=0.94,
            colour_g=0.82,
            colour_b=0.76
        )
        
    def rogers_ro3010(self):
        self.create_normal(
            name="Rogers RO3010 (lossy)",
            epsilon=11.2,
            mu=1.0,
            kappa=0.0,
            kappa_m=0.0,
            tand=0.0021,
            tand_freq=10.0,
            tand_given=True,
            tand_model="ConstTanD",
            tand_m=0.0,
            tand_m_freq=0.0,
            tand_m_given=False,
            tand_m_model="ConstKappa",
            rho=0.0,
            thermal_conductivity=0.95,
            colour_r=0.94,
            colour_g=0.82,
            colour_b=0.76
        )

    def copper(self):
        self.create_lossy_metal(
            name="Copper (pure)",
            mu=1.0,
            sigma=5.96e7,
            rho=8930.0,
            thermal_conductivity=401.0,
            specific_heat=390,
            youngs_modulus=120,
            poissons_ratio=0.33,
            thermal_expansion_rate=17,
            colour_r=1,
            colour_g=1,
            colour_b=0
        )


# ==================================================================
# BOOLEAN OPERATIONS CLASS
# ==================================================================
class Boolean:
    def __init__(self, project):
        self.project = project

    def subtract(self, component_a, solid_a, component_b, solid_b):
        history = f"""
Solid.Subtract "{component_a}:{solid_a}", "{component_b}:{solid_b}"
"""
        self.project.model3d.add_to_history(
            f"Python: Boolean Subtract {component_b}:{solid_b} to {component_a}:{solid_a}",
            history
        )
        
# ==================================================================
# PICK CLASS
# ==================================================================
class Pick:
    def __init__(self, project):
        self.project = project

    def face(self, component, solid, face_id):
        history = f"""
Pick.PickFaceFromId "{component}:{solid}", "{face_id}"
"""
        self.project.model3d.add_to_history(
            f"Python: Pick Face {face_id} from {component}:{solid}",
            history
        )