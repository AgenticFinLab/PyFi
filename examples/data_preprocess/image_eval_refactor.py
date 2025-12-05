from fttracer.tools.data_preprocess.image_eval_refactor import *

if __name__ == "__main__":

    input_dir = r"F:\AgenticFin_Lab\fttracer\data_colection_and_processing\processed_report\images_eval"
    output_dir_yes = r"F:\AgenticFin_Lab\fttracer\data_colection_and_processing\processed_report\images_eval_refactor_yes"
    output_dir_no = r"F:\AgenticFin_Lab\fttracer\data_colection_and_processing\processed_report\images_eval_refactor_no"

    process_json_files(input_dir, output_dir_yes, output_dir_no)
