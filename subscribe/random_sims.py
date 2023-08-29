# File made by ABEL LAGONELL - 7/31/2023

#Online Modules
import os, sys, glob
import traci
import traci.constants as tc
import pandas as pd
import datetime, logging
import copy, traceback
from random import choice
from optparse import OptionParser
import multiprocessing

#User-made Modules
sys.path.append("./../")
from postprocess import PostGraph, MultiCaptureGraph
from settings import Settings, GraphSetting
from traci_env import EnvironmentListener, BaseEnv, GreedyEnv, RandomEnv
from visualize import Visualize
from util import *

# Using the random destination this files is going to try to make sure that the simulations dont loop on themselves
#   as seen in a brief previuos tests.
# This file will take a lot from main_sim.py for the structure of the code and how it is going to be used.
# For the sake of simplicity this file will also not have a GUI component made

#Start Simulation and connect it to an object
def start_simulation(Env, sim_number, _seed=None, setting_obj=None, dir_name=None, main_env=None, new_players=False, label="default"):
    traci.start(["sumo", "-c", Settings.sumo_config], label=label )
    env = Env(sim_number=sim_number, _seed=_seed, setting_obj=setting_obj, main_env=main_env, new_players=new_players)
    conn = traci.getConnection(label=label)

    while True:
        conn.simulationStep()
        conn.addStepListener(env)
        if  env.break_condition:
            break

    print("veh successfully arrived ", env.sim_env.success_veh)

    return env.post_process, env

#Single Simulation Processor
def run(number=1, Env=EnvironmentListener, setting_obj=None, file_title=None, dir_name=None, main_env=None, new_players=False):
#number = Number of simulations, EnvL= Enviroments to be run, setting_obj= The Base settings of the simulation, dir_name= storage directory
    _seed = 3

    #Global MultiCapture
    multi_cap = MultiCaptureGraph("capture")

    #Processor
    post_process = PostGraph(file_title, columns=["sim_number", "sim_step", "veh_id", "edge_id", "speed", "capacity", "budget", "prev_poi", "algo"], dir_name=dir_name)

    sim_number=1

    while sim_number <= number:
        try:
            temp_process, env = start_simulation(Env, sim_number, _seed, setting_obj, dir_name, main_env, new_players, file_title)

            post_process.df_list = post_process.df_list + temp_process.df_list
            logging.info(f'SUCCESS FINISHED simulation {sim_number}')

            sim_number += 1

            env.sim_env.post_process_graph.setting = env.sim_env.GraphSetting
            multi_cap.simulation_list.append(env.sim_env.post_process_graph)

        except traci.exceptions.TraCIException as e:
            logging.info(f"FAILED simulation {sim_number} {str(e)}")

    multi_cap.pickle_save(os.path.join(dir_name, f'{file_title}.sim'))
    post_process.to_csv()

    return env

def kesselrun(start:int, end:int, inc:int, dir_name=None):
    main_env = None
    global_poi = None
    for i in range (start, end+inc, inc):
        mySetting = GraphSetting()
        mySetting.car_numbers = i
        mySetting.destination='random'

        if not main_env:
            main_env = run(1, BaseEnv, mySetting, f"{mySetting.car_numbers}_BASE", dir_name, main_env)
            global_poi = main_env.global_poi
        else:
            main_env.GraphSetting = mySetting
            main_env = run(1, BaseEnv, mySetting, f"{mySetting.car_numbers}_BASE", dir_name, main_env, True)
            main_env.global_poi = global_poi

        run(1, EnvironmentListener, mySetting, f"{mySetting.car_numbers}_ANTE", dir_name, main_env)
        run(1, RandomEnv, mySetting, f"{mySetting.car_numbers}_RAND", dir_name, main_env)
        run(1, GreedyEnv, mySetting, f"{mySetting.car_numbers}_GREE", dir_name, main_env)

if __name__ == '__main__':
    dt = datetime.datetime.utcnow().timestamp()
    dir_name = os.path.join(Settings.sim_save_path_graph, str(dt))
    os.mkdir(dir_name)
    print("making dir ", dir_name)

    logging.basicConfig(filename=os.path.join(dir_name, 'output.log'), filemode = 'w',format='%(asctime)s - %(name)s  - %(levelname)s - %(message)s', level=logging.INFO)

    kesselrun(5, 10, 5, dir_name)
