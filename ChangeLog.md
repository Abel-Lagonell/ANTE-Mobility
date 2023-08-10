#Changelog

## Version 2.1 : 2023-07-15

Deleted white spaces, and modified the import order for the following files

- _map.py
- env.py
- graph.py
- main_sim.py
- player/py
- postprocess.py
- settings.py
- traci_env.py
- util.py
- visualize.py

## Version 2.2 : 2023-08-03

Started work on the parallelization of the simulations.  
Continued work on the random destination of the cars but got stuck to a loop so switched over to parallelization.  

Minor changes to env.py to reflect the structure of the other file's importing structure.  
Also added a step by step guide on the README.md file of how the program can run with simple steps.  

## Version 2.3 : 2023-08-10

parallel_sims.py is a testing ground for the parallelization that helped in the controlling of the experiments. With it parallelization was able to be completed.  
Imported the finished version of the parallelization onto the main file of the github.  
Added comments onto the edited code  
