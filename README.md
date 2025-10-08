## Installation 

To use this code, you first need to clone this repository 

1 - Download anaconda (https://www.anaconda.com/download)

2 - Create a conda environment with python 3.9 (version matters for psychopy compatibility) 
```
conda create -n PMBR_env python=3.9
```

3 - Activate your environment
```
conda activate PMBR_env
```

4 - Install all required libraries by running with `pip` (psychopy version 2023.2.3 works for this code)

```
pip install --no-deps psychopy==2023.2.3
pip install -r requirements.txt
```


## Running 

1 - On an anaconda prompt terminal, navigate to your folder containing the task. (e.g. cd code/PMBR)

2 - Run the task by running the following command in the terminal (don't forget to activate environment)
```
python PMBR.py
```
3 - Enter the task parameters on the pop up GUI. In the `Set` entry chose practice for practice mode, and standard for the task
