""" Reduces videos to target number, randomizes distribution of pass counts, renames files """

import os
import random
import shutil
from collections import defaultdict


def collect_pass_counts(folder):
    """ 
    Generates dictionary of midline-pass-counts and video filepaths that have those counts.
    Organizes videos by midline-pass-counts for calculated removal.
    """

    pass_counts_dict = {}
    video_folders = set()
    
    for root, dirs, files in os.walk(folder, topdown=False):
        if 'select.txt' in files:
            select_file_path = os.path.join(root, 'select.txt')
            parent_folder_path = os.path.dirname(root)
            with open(select_file_path, 'r') as f:
                for line in f:
                    parts = line.split(',')
                    if len(parts) > 1:
                        try:
                            count = int(parts[1].strip())
                            if count not in pass_counts_dict:
                                pass_counts_dict[count] = []
                            pass_counts_dict[count].append(parent_folder_path)
                            video_folders.add(parent_folder_path)
                        except ValueError:
                            continue

    pass_counts_dict = dict(sorted(pass_counts_dict.items()))

    return pass_counts_dict, video_folders


def generate_bin_counts(pass_counts_dict):
    """ Generates a list with counts of videos in each midline-pass-count bin. """

    max_count = max(pass_counts_dict.keys())
    bin_counts = [0] * (max_count + 1)

    for count, folders in pass_counts_dict.items():
        bin_counts[count] = len(folders)

    return bin_counts


def calculate_removals_per_bin(bin_counts, target_video_count):
    """ 
    Generates a list determining how many videos 
    are to be removed from each bin to make distribution of midline-pass counts uniform. 
    """

    total_videos = sum(bin_counts)
    videos_to_remove = total_videos - target_video_count

    # Initialize a list to keep track of removals per bin
    removals_per_bin = [0] * len(bin_counts)

    while videos_to_remove > 0:
        # Identify the highest and second-highest values in bin_counts
        max_val = max(bin_counts)
        second_max_val = max(val for val in bin_counts if val < max_val)

        # Determine the indices of the bins with the max value
        max_indices = [i for i, val in enumerate(bin_counts) if val == max_val]

        # Calculate how much to reduce in this iteration
        reduce_by = min(max_val - second_max_val, videos_to_remove)

        # Distribute the reduction evenly across all bins with the max value
        per_bin_reduction = reduce_by // len(max_indices)
        extra_reduction = reduce_by % len(max_indices)

        for i in max_indices:
            bin_counts[i] -= per_bin_reduction
            removals_per_bin[i] += per_bin_reduction
            videos_to_remove -= per_bin_reduction

        # Handle any remainder in reduction
        for i in range(extra_reduction):
            bin_counts[max_indices[i]] -= 1
            removals_per_bin[max_indices[i]] += 1
            videos_to_remove -= 1

        # Stop reducing if removed enough videos
        if videos_to_remove <= 0:
            break

    # Return the final list of removals per bin
    return removals_per_bin


def select_videos_to_remove(pass_counts_dict, removals_per_bin):
    """ Randomly selects videos from each bin of midline-pass-counts to remove based on removal list. """

    videos_to_remove = []

    for i, num_to_remove in enumerate(removals_per_bin):
        if num_to_remove > 0:
            selected_folders = random.sample(pass_counts_dict[i], num_to_remove)
            videos_to_remove.extend(selected_folders)

    assert len(videos_to_remove) == sum(removals_per_bin), "Mismatch in removal counts"

    return videos_to_remove


def remove_folders(folders_to_remove):
    """ Remove selected videos and their parent folders. """

    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            # print(f"Removed folder: {folder}")
    print("Removals complete.")


# Based on parent folder > subfolder 1 ("6", "12"), > subfolders with videos > locs > select.txt files organization
def rename_folders_and_files(parent_folder):    
    """ Renumber and rename files based on reduced items. """

    for subfolder1 in os.scandir(parent_folder):
        if subfolder1.is_dir():
            subfolder2_list = [f for f in os.scandir(subfolder1.path) if f.is_dir()]
            subfolder2_list.sort(key=lambda x: os.path.basename(x.path))
            
            for idx, subfolder2 in enumerate(subfolder2_list):
                subfolder2_path = subfolder2.path
                subfolder2_name = os.path.basename(subfolder2_path)
                new_number = f"{idx:03}"
                new_subfolder2_name = f"{subfolder2_name[:subfolder2_name.rfind('_')+1]}{new_number}"
                new_subfolder2_path = os.path.join(subfolder1.path, new_subfolder2_name)
                
                if os.path.exists(new_subfolder2_path):
                    print(f"Directory already exists: {new_subfolder2_path}")
                    continue
                
                os.rename(subfolder2_path, new_subfolder2_path)
                print(f"Renamed folder {subfolder2_path} to {new_subfolder2_path}")
                
                # Rename video files
                for file in os.listdir(new_subfolder2_path):
                    file_path = os.path.join(new_subfolder2_path, file)
                    
                    if file.endswith('.mp4'):
                        new_file_name = f"{file[:file.rfind('_')+1]}{new_number}.mp4"
                        new_file_path = os.path.join(new_subfolder2_path, new_file_name)
                        os.rename(file_path, new_file_path)
                        print(f"Renamed file {file_path} to {new_file_path}")
                        
                # Rename select.txt files
                locs_path = os.path.join(new_subfolder2_path, 'locs')
                if os.path.isdir(locs_path):
                    for file in os.listdir(locs_path):
                        if file == 'select.txt':
                            select_file_path = os.path.join(locs_path, file)
                            new_select_name = f'select_{new_number}.txt'
                            new_select_path = os.path.join(locs_path, new_select_name)
                            os.rename(select_file_path, new_select_path)
                            print(f"Renamed file {select_file_path} to {new_select_path}")


def execute_changes(filepath, target_video_count):
    """ Runs all functions to reduce videos down to target count and blunt normal distribution peak. """

    print("Final Results")

    # Generates midline-pass-count dictionary and confirms initial # of folders
    pass_counts_dict, video_folders = collect_pass_counts(filepath)
    total_videos_in_folder = len(video_folders)
    print(f"Total videos in folder: {total_videos_in_folder}")
    
    # Generates midline-pass-count bin counts list and confirms initial # of folders and bins
    bin_counts = generate_bin_counts(pass_counts_dict) 
    print("Bin counts: " + str(bin_counts))
    print("Sum of Bin counts: " + str(sum(bin_counts)))
    print("# of bins: " + str(len(bin_counts)))

    # Calculates number of removals per bin and confirms count
    removals_per_bin = calculate_removals_per_bin(bin_counts, target_video_count)
    print("Removals per Bin: " + str(removals_per_bin))
    print("Sum of Removals per Bin: " + str(sum(removals_per_bin)))
    print("# of bins: " + str(len(removals_per_bin)))
    
    # Selects and removes videos based on calculations
    videos_to_remove = select_videos_to_remove(pass_counts_dict, removals_per_bin)
    remove_folders(videos_to_remove)

    # Renames remaining folders and files within
    rename_folders_and_files(filepath)


target_video_count = 110

# Change above folder_path manually from list below
# Turn into iterable execution on final implementation
# Running one at a time ensure right # of folders deleted

# Working on: No Target videos
folders_to_process = [
    "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_Reduced-Renamed/Gradient_Balls_H_Merged",
    "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_Reduced-Renamed/Gradient_Balls_V_Merged",
    "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_Reduced-Renamed/Curves",
    "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_Reduced-Renamed/Lines"
]

# def main(folders_to_process, target_video_count):
#     for folder in folders_to_process:
#         folder_path = folder
#         execute_changes(folder_path, target_video_count)

# main(folders_to_process, target_video_count)


filepath = "/Users/nandinibohra/Downloads/Final_Videos_NoTarget/Final_Videos_NoTarget_Reduced-Renamed/Gradient_Balls_H_Merged"


rename_folders_and_files(filepath)