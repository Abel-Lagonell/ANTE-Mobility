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

# Using traci.start() and traci.getConnection we want to run multiple simulations at the same time 
#    and see if there is any benifit to doing so at both a large and small scale.
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
def run(number=1, Env=EnvironmentListener, setting_obj=None, file_title=[str], dir_name=None, main_env=None, label="default", new_players=False):
#number = Number of simulations, EnvL= Enviroments to be run, setting_obj= The Base settings of the simulation, dir_name= storage directory
    _seed = 3

    #Global MultiCapture
    multi_cap = MultiCaptureGraph("capture")

    #Processor
    post_process = PostGraph(file_title, columns=["sim_number", "sim_step", "veh_id", "edge_id", "speed", "capacity", "budget", "prev_poi", "algo"], dir_name=dir_name)

    sim_number=1

    while sim_number <= number:
        try:
            temp_process, env = start_simulation(Env, sim_number, _seed, setting_obj, dir_name, main_env, new_players, label)

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

        if not main_env:
            main_env = run(1, BaseEnv, mySetting, f"{mySetting.car_numbers}_BASE", dir_name, main_env, f"{i}_BASE")
            global_poi = main_env.global_poi
        else:
            main_env.GraphSetting = mySetting
            main_env = run(1, BaseEnv, mySetting, f"{mySetting.car_numbers}_BASE", dir_name, main_env, f"{i}_BASE", True)
            main_env.global_poi = global_poi

        p1 = multiprocessing.Process(target = run, args = (1, EnvironmentListener, mySetting, f"{mySetting.car_numbers}_ANTE", dir_name, main_env, f"{i}_ANTE"))
        p2 = multiprocessing.Process(target = run, args = (1, RandomEnv, mySetting, f"{mySetting.car_numbers}_RAND", dir_name, main_env, f"{i}_RAND"))
        p3 = multiprocessing.Process(target = run, args = (1, GreedyEnv, mySetting, f"{mySetting.car_numbers}_GREE", dir_name, main_env, f"{i}_GREEDY"))

        p1.start()
        p2.start()
        p3.start()

        p1.join()
        p2.join()
        p3.join()

def inc_cap(start:int, end:int, inc:int, dir_name=None): #Changing the storage capacity of the players
    main_env=None

    for i in range (start, end+inc, inc):
        mySetting = GraphSetting()
        mySetting.player_capacity_random = (i, mySetting.player_capacity_random[1])

        if not main_env:
            main_env=run(1, BaseEnv, mySetting, f"{mySetting.player_capacity_random[0]}_BASE", dir_name, main_env, f"{mySetting.player_capacity_random[0]}_BASE")
        else:
            main_env.GraphSetting = mySetting
            main_env.change_capacity()
            run(1, BaseEnv, mySetting, f"{mySetting.player_capacity_random[0]}_BASE", dir_name, main_env, f"{mySetting.player_capacity_random[0]}_BASE")


        p1 = multiprocessing.Process(target = run, args =(1, EnvironmentListener, mySetting, f"{mySetting.player_capacity_random[0]}_ANTE", dir_name, main_env, f"{mySetting.player_capacity_random[0]}_ANTE"))
        p2 = multiprocessing.Process(target = run, args =(1, RandomEnv, mySetting, f"{mySetting.player_capacity_random[0]}_RAND", dir_name, main_env, f"{mySetting.player_capacity_random[0]}_RAND"))
        p3 = multiprocessing.Process(target = run, args =(1, GreedyEnv, mySetting, f"{mySetting.player_capacity_random[0]}_GREE", dir_name, main_env, f"{mySetting.player_capacity_random[0]}_GREE"))
        p1.start()
        p2.start()
        p3.start()

    main_env.reward_to_json(dir_name)

if __name__ == '__main__':
    dt = datetime.datetime.utcnow().timestamp()
    dir_name = os.path.join(Settings.sim_save_path_graph, str(dt))
    os.mkdir(dir_name)
    print("making dir ", dir_name)

    logging.basicConfig(filename=os.path.join(dir_name, 'output.log'), filemode = 'w',format='%(asctime)s - %(name)s  - %(levelname)s - %(message)s', level=logging.INFO)

    #kesselrun(5, 10, 5, dir_name)
    inc_cap(10, 90, 20, dir_name)
