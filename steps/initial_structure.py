from common_structures import *

def build_initial_structure(model, metallization_t_mm, board_w_mm, board_l_mm,
                            resonator_type_1, dims_1, position_1, name_1,
                            resonator_type_2, dims_2, position_2, name_2,
                            tube_inner_diam_mm, tube_outer_diam_mm):  
    
    carve_sensor(model=model, metallization_t_mm=metallization_t_mm, board_w_mm=board_w_mm, board_l_mm=board_l_mm,
                  resonator_type_1=resonator_type_1, dims_1=dims_1, position_1=position_1, name_1=name_1,
                  resonator_type_2=resonator_type_2, dims_2=dims_2, position_2=position_2, name_2=name_2)
    
    build_tubes(model=model, tube_inner_radius_mm=tube_inner_diam_mm/2, tube_outer_radius_mm=tube_outer_diam_mm/2,
                board_w_mm=board_w_mm, metallization_t_mm=metallization_t_mm,
                SC1_y1=position_1["y"], SC1_y2=position_1["y"]-dims_1["separation"], SC2_y=position_2["y"]) 
    
def run_and_save_initial(mws_prj, simulation, OUTPUT_DIR, filename):
    """Runs the solver and saves S-parameter CSVs. Returns df_db."""
    simulation.run()
    cst_path = mws_prj.filename()
    df_db      = simulation.results.get_s_parameters(cst_path, magnitude="db", AR_filter=True)
    df_complex = simulation.results.get_s_parameters(cst_path, magnitude="complex", AR_filter=True)
    df_db.to_csv(     rf"{OUTPUT_DIR}\{filename}_db.csv")
    df_complex.to_csv(rf"{OUTPUT_DIR}\{filename}_complex.csv")
    print(f"  Saved: {OUTPUT_DIR}\\{filename}_db.csv")
    print(f"  Saved: {OUTPUT_DIR}\\{filename}_complex.csv")
    return df_db

