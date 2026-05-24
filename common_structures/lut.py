def create_lut(model, name, component="LUT", 
               inner_radius=1.0, outer_radius=2.0, 
               x_min=0, x_max=1, center_y=0, center_z=0):
    
    model.geometry.cylinder(name=name+'_Silicon', component=component, material="Silicon (lossy)", 
                            outer_radius=outer_radius, inner_radius=inner_radius,
                            axis="x", axis_min=x_min, axis_max=x_max, center_1=center_y, center_2=center_z)

    model.geometry.cylinder(name=name+'_Water', component=component, material="Water", 
                        outer_radius=inner_radius, inner_radius=0.0,
                        axis="x", axis_min=x_min, axis_max=x_max, center_1=center_y, center_2=center_z)