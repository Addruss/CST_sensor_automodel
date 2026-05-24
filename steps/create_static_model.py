def define_materials(model):
    model.material.rogers_ro4003c()
    model.material.copper()
    model.material.silicon_lossy()
    model.material.water()

def create_static_geometry(model, board_w_mm, board_l_mm, substract_h_mm, TL_w_mm, metallization_t_mm):
    # Substrate
    model.geometry.brick(
        name="substract", component="sensor",
        material="Rogers RO4003C (lossy)",
        x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2),
        y_min=-(board_l_mm / 2), y_max=(board_l_mm / 2),
        z_min=0,                  z_max=substract_h_mm
    )

    # Transmission line
    model.geometry.brick(
        name="TL", component="sensor",
        material="Copper (pure)",
        x_min=-(TL_w_mm / 2), x_max=(TL_w_mm / 2),
        y_min=-(board_l_mm / 2), y_max=(board_l_mm / 2),
        z_min=substract_h_mm,
        z_max=substract_h_mm + metallization_t_mm
    )

    # Ground plane (initial — rebuilt each SA iteration)
    model.geometry.brick(
        name="GND", component="sensor",
        material="Copper (pure)",
        x_min=-(board_w_mm / 2), x_max=(board_w_mm / 2),
        y_min=-(board_l_mm / 2), y_max=(board_l_mm / 2),
        z_min=-metallization_t_mm, z_max=0
    )

def create_ports(model, simulation):
    # Port 1:
    model.pick.face("sensor", "TL", 3)
    simulation.port.create_port_from_pick(port_number=1,
                    x_range_add_min="1.27*5.58", x_range_add_max="1.27*5.58",
                    z_range_add_min="1.27", z_range_add_max="1.27*5.58")
    # Port 2:
    model.pick.face("sensor", "TL", 5)
    simulation.port.create_port_from_pick(port_number=2, 
                    x_range_add_min="1.27*5.58", x_range_add_max="1.27*5.58",
                    z_range_add_min="1.27", z_range_add_max="1.27*5.58")