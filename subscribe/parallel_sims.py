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

#Single Simulation
def start_simulation(Env, sim_number, _seed=None, setting_obj=None, dir_name=None, main_env=None, new_players=False):
    traci.start(["sumo", "-c", Settings.sumo_config])
    env = Env(sim_number=sim_number, _seed=_seed, setting_obj=setting_obj, main_env=main_env, new_players=new_players)
    conn = traci.getConnection(label="default")

    return conn, env

def base_run(Env, setting_obj=None,dir_name=None, file_title=None):
    _seed =3

    #File System Handler
    post_process = PostGraph(file_title, columns=["sim_number", "simstep", "veh_id", "edge_id", "speed", "capacity", "budget", "prev_poi","algo"], dir_name=dir_name)

    #Global MultiCapture
    multi_cap = MultiCaptureGraph("capture")

    try:
        temp_conn, env = start_simulation(Env, 1, _seed, setting_obj, dir_name)
        while True:
            temp = step_sim(temp_conn, env)
            if temp: break

        post_process.df_list = post_process.df_list + env.post_process.df_list
        logging.info(f'SUCCESS FINISHED simulation {sim_number}')

        env.sim_env.post_process_graph.setting = env.sim_env.GraphSetting
        multi_cap.simulation_list.append(env.sim_env.post_process_graph)

    except traci.exceptions.TraCIException as e:
        logging.info(f"Failed simulation {sim_number} {str(e)}")
        traci.close()

    multi_cap.pickle_save(os.path.join(dir_name, f'{file_title}.sim'))
    post_process.to_csv()
    traci.close()

    return env

#Multi Simulation Handler
def run(number=1, EnvL=[EnvironmentListener], setting_obj=None, file_title=[str], dir_name=None, main_env=None):
#number = Number of simulations, EnvL= Enviroments to be run, setting_obj= The Base settings of the simulation, dir_name= storage directory
    _seed = 3

    bool_list=[bool]
    conn_list=[]
    env_list=[]


    #Global MultiCapture
    multi_cap = MultiCaptureGraph("capture")

    sim_number=1

    main_env = base_run(BaseEnv, setting_obj=setting_obj, file_title=file_title.pop(0), dir_name=None)

    while sim_number <= number:

        try:
            for env_sim in Env:
                conn, env = start_simulation(Env, sim_number, _seed=_seed, setting_obj=setting_obj, dir_name=dir_name, new_players=new_players, main_env =main_env)
                conn_list.append(conn)
                env_list.append(env)
                bool_list.append(False)

            while all(bool_list):
                for i in len(conn_list):
                    bool_list[i] = step_sim(conn_list[i], env_list[i])

            for i in len(env_list):
                #File System Handler
                post_process = PostGraph(file_title, columns=["sim_number", "simstep", "veh_id", "edge_id", "speed", "capacity", "budget", "prev_poi"], dir_name=dir_name)
                post_process.df_list = post_process.df_list + env.post_process.df_list
                env.sim_env.post_process_graph.setting = env.sim_env.GraphSetting
                multi_cap.simulation_list.append(env.sim_env.post_process_graph)

            logging.info(f'SUCCESS FINISHED simulation {sim_number}')
            sim_number+= 1

        except traci.exceptions.TraCIException as e:
            logging.info(f"Failed simulation {sim_number} {str(e)}")
            traci.close()

def step_sim(conn_obj, env_obj):
    if env.break_condition:
        return True
    conn_obj.simulationStep()
    conn_obj.addStepListener(env_obj)
    if env.break_condition:
        return True

if __name__ == '__main__':
    mySetting = GraphSetting()
    mySetting.car_numbers = 10
    file_title = ["10_BASE","10_ANTE","10_GREEDY","10_RANDOM"]
    Env = [EnvironmentListener, GreedyEnv, RandomEnv]

    dt = datetime.datetime.utcnow().timestamp()
    dir_name = os.path.join(Settings.sim_save_path_graph, str(dt))
    os.mkdir(dir_name)
    logging.basicConfig(filename=os.path.join(dir_name, 'output.log'), filemode = 'w',format='%(acstime)s - %(name)s  - %(levelname)s - %(message)s', level=logging.INFO)

    run(EnvL=Env,setting_obj=mySetting, number =1, file_title=file_title, dir_name = dir_name)
