## Introduction 
This code implements the Post-Movement Beta Rebound (PMBR) joystick task, described in _Muralidharan V, Aron AR. Behavioral Induction of a High Beta State in Sensorimotor Cortex Leads to Movement Slowing. J Cogn Neurosci. 2021 Jun 1;33(7):1311-1328. doi: 10.1162/jocn_a_01717_
This task investigates the slowing of a movement iniation when occuring within the time window of a PMBR following an ipsilateral movement. 

## Prerequesites
- You will need 2 PC-compatible joysticks. We used the Thrustmaster T.16000M as they come with right- and left-handed configurations.
- Even though the task would work with one screen, it is optimised for a two-screens configuration. One participant screen and one experimenter screen.
   
## Installation 

To use this code, you first need to clone this repository 

1 - Download and install anaconda distribution (https://www.anaconda.com/download)

2 - Open an anaconda prompt terminal and create a conda environment with python 3.9 (version matters for psychopy compatibility) 
```
conda create -n PMBR_env python=3.9
```

3 - Activate your environment
```
conda activate PMBR_env
```
You should see <PMBR_env> at the beginning of the prompt  


4 - Inside your terminal, navigate to the folder containing this repo and install all required libraries by using `pip` (psychopy version 2023.2.3 works for this code)

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


Developped by Paul de Fontenay, MSc and Andràs Puszka, MD, PhD

