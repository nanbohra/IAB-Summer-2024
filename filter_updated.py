#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : filter.py
@Time    : 
@Author  : Adapted from Yang Shen's code
@Contact : 
@Version : 0.1
@License : None
@Desc    : None
'''

import os
import shutil
import json

import tabulate
import numpy as np


def filter(json_file_path):
    js_wkdir = os.path.dirname(json_file_path)
    loc_dir = os.path.join(js_wkdir, "locs")
    os.makedirs(loc_dir, exist_ok=True)
    with open(json_file_path, "r") as fp:
        data = json.load(fp)
        num_balls = int(data["metadata"]["num_balls"])
        num_frames = int(data["metadata"]["duration"]) * \
            int(data["metadata"]["fps"])
        for i in range(num_balls):
            ball_id = "ball_" + str(i)
            with open(os.path.join(loc_dir, ball_id + ".txt"), "w") as fp:
                for j in range(num_frames):
                    x, y = data[str(j)][i]["loc"]
                    fp.write(f"{x},{y},{j}\n")
    return 

def target_filter(json_file_path):
    js_wkdir = os.path.dirname(json_file_path)
    loc_dir = os.path.join(js_wkdir, "locs")
    os.makedirs(loc_dir, exist_ok=True)
    with open(json_file_path, "r") as fp:
        data = json.load(fp)
        num_balls = int(data["metadata"]["num_balls"])
        num_frames = int(data["metadata"]["duration"]) * \
            int(data["metadata"]["fps"])
        with open(os.path.join(loc_dir, "target.txt"), "w") as fp:
            for j in range(num_frames):
                if len(data[str(j)]) == num_balls + 1:
                    x, y = data[str(j)][num_balls]["loc"]
                    fp.write(f"{x},{y},{j}\n")

    if os.path.getsize(os.path.join(loc_dir, "target.txt")) == 0:
        os.remove(os.path.join(loc_dir, "target.txt"))

    return

# Use for non-problematic json files, original script
def ecc_filter(json_file_path):
    js_wkdir = os.path.dirname(json_file_path)
    loc_dir = os.path.join(js_wkdir, "locs")
    os.makedirs(loc_dir, exist_ok=True)

    with open(json_file_path, "r") as fp:
        data = json.load(fp)
        num_balls = int(data["metadata"]["num_balls"])
        num_frames = int(data["metadata"]["duration"]) * \
            int(data["metadata"]["fps"])
    
        # Get the target ball info and distractor info:
        #  [[x, y], ..., [x_target, y_target]]
        locs = [] # Container for each frame
        for j in range(num_frames):
            if len(data[str(j)]) == num_balls +1:
                locs.append([data[str(j)][i]["loc"] for i in range(num_balls +1)])

        locs = np.array(locs)
        print("locs shape:", locs.shape)

        if locs.size != 0:
            # Get the ecc of each distractor ball
            distractors = locs[:, :-1, :]
            tracking = locs[:, -1:, :]
            ecc = np.linalg.norm(distractors - tracking, axis=2)
            # Calculate the mean of each ball
            mean_values = np.mean(ecc, axis=0)

            # Calculate the median of each ball
            median_values = np.median(ecc, axis=0)

            # Calculate the standard deviation of each ball
            std_values = np.std(ecc, axis=0)

            # Calculate the minimum of each ball
            min_values = np.min(ecc, axis=0)

            # Calculate the maximum of each ball
            max_values = np.max(ecc, axis=0)

            static_data = {
                "id": [i for i in range(num_balls)],
                "min": min_values,
                "mean": mean_values,
                "median": median_values,
                "std": std_values,
                "max": max_values
            }
            with open(os.path.join(loc_dir, "distance.log"), "w") as fp:
                fp.write(tabulate.tabulate(static_data, headers="keys", tablefmt="github"))

        """ When I need to FILTER files and generate txt (with target conditions). """
        # flag = False
        # tracking_idx = num_balls-1
        # with open(os.path.join(loc_dir, "select.txt"), "w") as f:
        # # if True:
        #     # print(f"Working on {json_file_path}")
        #     # for idx in range(num_balls):
        #         if 150 > min_values[tracking_idx] > 100:
        #             pass_ts = pass_counter(data, tracking_idx)
        #             f.write(f"{tracking_idx}, {len(pass_ts)}, {pass_ts}\n")
        #             flag = True
        #             # print(f"Ball {idx} is selected with min value {min_values[idx]}")
        #             # fp.write(f"{ecc[j, idx]}\n")
        
        # if not flag:
        #     # os.remove(os.path.join(loc_dir, "select.txt"))
        #     parent_dir = os.path.dirname(loc_dir)
        #     # os.rmdir(parent_dir)
        #     shutil.rmtree(parent_dir)


        """ 
        When I need to generate txt files for ALL videos (e.g. no target or in-lab files)
         If need to count midline passes for tracking, change pass-count to tracking_idx 
        """

        tracking_idx = num_balls-1
        with open(os.path.join(loc_dir, "select.txt"), "w") as f:
            # print(f"Working on {json_file_path}")
            # for idx in range(num_balls):
                # if 150 > min_values[tracking_idx] > 100:
                    pass_ts = pass_counter(data, tracking_idx)
                    f.write(f"{tracking_idx}, {len(pass_ts)}, {pass_ts}\n")
                    # print(f"Ball {idx} is selected with min value {min_values[idx]}")
                    # fp.write(f"{ecc[j, idx]}\n")
        

    return



# Checks if the ball passes the midline
def pass_counter(json_data, idx):
    midline = 1080 / 2
    pass_ts = []
    num_balls = int(json_data["metadata"]["num_balls"])
    num_frames = int(json_data["metadata"]["duration"]) * \
        int(json_data["metadata"]["fps"])
    locs = []
    for j in range(num_frames):
        locs.append([json_data[str(j)][i]["loc"] for i in range(num_balls)])
    # locs.shape: num_frames X N X 2    
    locs = np.array(locs)
    for j in range(num_frames - 1):
        if (locs[j, idx, 1] - midline) * (locs[j + 1, idx, 1] - midline) < 0:
            pass_ts.append(j)
    return pass_ts


def main(wkdir):
    for root, _, files in os.walk(wkdir):
        for f in files:
            if f.endswith(".json"):
                js_fp = os.path.join(root, f)
                filter(js_fp)
                target_filter(js_fp)
                ecc_filter(js_fp)


if __name__=="__main__":
    # wkdir = "/home/shenyang/projects/blenderSimu/iabSimu/pygame/data/iab_test_set_v3_download"
    # main(wkdir=wkdir)
    # fp = "/home/shenyang/projects/blenderSimu/iabSimu/pygame/data/iab_test_set_v1/Gradient_Balls_H/12/Gradient_Balls_H_0002/data.json"
    # ecc_filter(fp)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--wkdir", type=str, default="/home/shenyang/projects/blenderSimu/iabSimu/pygame/data/iab_test_set_v3_download")
    args = parser.parse_args()
    main(wkdir=args.wkdir)

# cmd line input: python filter.py --wkdir /path/to/folder



"""
- 
"""

