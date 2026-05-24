from .resonator import *
from .lut import *

def carve_sensor(model, metallization_t_mm, board_w_mm, board_l_mm, 
                 resonator_type_1, dims_1, position_1, name_1, 
                 resonator_type_2, dims_2, position_2, name_2
                 ):
    
    # Delete previous slots and GND
    model.geometry.delete_solid("sensor", "GND")

    # Create new GND plane
    model.geometry.brick(
        name="GND", component="sensor",
        material="Copper (pure)",
        x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2),
        y_min=-(board_l_mm / 2), y_max=(board_l_mm / 2),
        z_min=-metallization_t_mm, z_max=0
    )

    # Carve resonator cell 1 (low-frequency supercell) 
    create_cell(model, resonator_type_1, dims_1, position_1, name_1, metallization_t_mm)

    # Carve resonator cell 2 (high-frequency supercell)
    create_cell(model, resonator_type_2, dims_2, position_2, name_2, metallization_t_mm)

def build_tubes(model, tube_inner_radius_mm, tube_outer_radius_mm, board_w_mm, 
                SC1_y1, SC1_y2, SC2_y, metallization_t_mm):
    # Create LUT tubes
    # for SC1
    create_lut(model, name="SC1_LUT1", component="LUT", 
               inner_radius=tube_inner_radius_mm, outer_radius=tube_outer_radius_mm, 
               x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2), 
               center_y=SC1_y1, center_z=-(metallization_t_mm+tube_outer_radius_mm))
    
    create_lut(model, name="SC1_LUT2", component="LUT", 
               inner_radius=tube_inner_radius_mm, outer_radius=tube_outer_radius_mm, 
               x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2), 
               center_y=SC1_y2, center_z=-(metallization_t_mm+tube_outer_radius_mm))
        
    # for SC2
    create_lut(model, name="SC2_LUT1", component="LUT", 
               inner_radius=tube_inner_radius_mm, outer_radius=tube_outer_radius_mm, 
               x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2), 
               center_y=SC2_y, center_z=-(metallization_t_mm+tube_outer_radius_mm))
    
def delete_tubes(model):
    model.geometry.delete_solid("LUT", "SC1_LUT1_Silicon")
    model.geometry.delete_solid("LUT", "SC1_LUT2_Silicon")
    model.geometry.delete_solid("LUT", "SC2_LUT1_Silicon")
    model.geometry.delete_solid("LUT", "SC1_LUT1_Water")
    model.geometry.delete_solid("LUT", "SC1_LUT2_Water")
    model.geometry.delete_solid("LUT", "SC2_LUT1_Water")