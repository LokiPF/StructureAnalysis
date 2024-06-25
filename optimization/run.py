import h5py
import numpy as np
import os
import time

with open("./fem_template.template", "r") as f:
    fem_template = f.read()

# ply_angles = [0, 15, 30, 45, 60, 75, -15, -30, -45, -60, -75]
ply_angles = [0, 75, 75, 60, 0, 15, 45, 45]


def get_max_displacement():
    with  h5py.File("./ASE_Project2024_SuperPanel.h5", 'r') as f:
        displacement = np.min(f['OPTISTRUCT/RESULT/NODAL/DISPLACEMENT'][:]['Z'])
        test = f['OPTISTRUCT/RESULT/NODAL/STRESS'][:]['Z']

    return abs(displacement)

def get_min_reserve_factor():
    with h5py.File("./analyze/CFRP Beam v10.h5", 'r') as f:
        displacement = np.min(f['OPTISTRUCT/RESULT/NODAL/DISPLACEMENT'][:]['Z'])

    return abs(displacement)


def edit_fem_file(t, dim1, dim2, dim3, dim4):
    new_plies = fem_template.format(
        t=t,
        dim1=dim1,
        dim2=dim2,
        dim3=dim3,
        dim4=dim4
    )

    with open("./ASE_Project2024_SuperPanel_redesign_03771075.fem", "w") as f:
        f.write(new_plies)


def run_optistruct():
    # cd to "analyze" folder
    batch_file = "C:\\Program Files\\Altair\\2023.1\\hwsolvers\\scripts\\optistruct.bat"
    os.system(f'cd analyze && "{batch_file}" "CFRP Beam v10.fem" -nt 12 > nul 2>&1')


if __name__ == "__main__":
    # angle search space
    {
        "top": [0, 15],
        "load": [0, 15, 45, 75, 90],
        "web": [0, 15, 45, 75, 90],
        "webmiddle": [0, 15, 45, 75, 90],
        "bottom": [0, 15],
        "bottommiddle": [0, 15, 45, 60],
        "support1": [0, 15, 45, 75, 90],
        "support2": [0, 15, 45, 75, 90],
    }
    # search space

    dimensions = [5, 15, 30, 45, 60, 75, 90]
    defaults = [5, 45, 45, 45, 45]

    # for load, web, webmiddle, bottommiddle, support1 and support2 try the different angles and keep the best one, then move on to the next one
    # for top and bottom keep the angle fixed at 0
    # search space
    angles = defaults
    best = 20
    for working_index in (1, 2, 3, 5, 6, 7):
        for dim in dimensions:
            start = time.time()
            angles[working_index] = dim

            t, dim1, dim2, dim3, dim4 = defaults
            edit_fem_file(t, dim1, dim2, dim3, dim4)
            run_optistruct()
            displacement = get_max_displacement()

            with open("results.txt", "a") as f:
                f.write(
                    f"t: {t}, dim1: {dim1}, dim2: {dim2}, dim3: {dim3}, dim4: {dim4}, Displacement: {displacement}\n")

            if displacement < best:
                # new best, set default to this angle
                best = displacement
                defaults[working_index] = dim

            print("Time taken: ", time.time() - start)

        angles[working_index] = defaults[working_index]

        # print(f"Top: {top}, Load: {load}, Web: {web}, Webmiddle: {webmiddle}, Bottom: {bottom}, Bottommiddle: {bottommiddle}, Support1: {support1}, Support2: {support2}")
        # edit_fem_file(top, load, web, webmiddle, bottom, bottommiddle, support1, support2)
        # run_optistruct()
        # displacement = get_max_displacement()
        # print(f"Displacement: {displacement}")
        # with open("results.txt", "a") as f:
        #     f.write(f"Top: {top}, Load: {load}, Web: {web}, Webmiddle: {webmiddle}, Bottom: {bottom}, Bottommiddle: {bottommiddle}, Support1: {support1}, Support2: {support2}, Displacement: {displacement}\n")
