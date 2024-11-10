""" Creates summary midline_pass_counts.txt file from all select.txt files of individual videos """

import os

def summarize_selects(folder_path):
    """ Creates a table of video index and midline pass count in each video. """

    output_file_path = os.path.join(folder_path, 'midline_pass_counts.txt')
    
    with open(output_file_path, 'w') as output_file:
        # Write header
        output_file.write('Index,Value\n')
        
        index = 0  # Change here if indexing needs to start differently
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith('.txt') and filename != 'midline_pass_counts.txt':
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    if len(lines) > 0:
                        parts = lines[0].strip().split(',')

                        if len(parts) > 1:
                            value = parts[1].strip()

                            output_file.write(f"{index},{value}\n")
                            index += 1  

    print(f"Table generated and saved to {output_file_path}")


folder_path = "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_VideosOnly/Curves/curves_select.txts"

summarize_selects(folder_path)


