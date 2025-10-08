'''This script implements a joystick task for the PMBR experiment.
Structure was adapted from https://github.com/celstark/MST/blob/71af39c5dc2e157e0059432aa505dda4670420e6/MST_Continuous_PsychoPy.py
Paul de Fontenay, UPHUMMEL EPFL, 2025
'''

import numpy as np
import csv
import os
from psychopy import visual, core, tools, event, sound, parallel
from psychopy import gui
from datetime import datetime
from pathlib import Path
import argparse
import random
from psychopy.hardware import joystick
import time


#Get screen arguments
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--monitor", default=1)
args = parser.parse_args()
n_screen = int(args.monitor)


#Set parallel port address for triggers
parallel.setPortAddress(address=0xD010)




def send_trigger(pin):
    """
    Sends a short digital trigger pulse through a specified pin on the parallel port.
    
    This function sets the given `pin` high (1) for 50 milliseconds, then sets it back to low (0).
    It is typically used to send event markers (triggers) to external devices (e.g., EEG systems, DAQ)
    at specific moments in an experiment.

    Note:
        Only pin #2 is typically used for TI in this specific setup.

    Args:
        pin (int): The parallel port pin number to activate.
    """
    parallel.setPin(pin,1)
    time.sleep(0.05)
    parallel.setPin(pin,0)




def get_parameters(skip_gui=False):
    """
    Retrieves and returns experiment parameters from a GUI popup window or saved file.

    If `skip_gui` is False, the function displays a GUI dialog for the user to input
    experiment parameters such as participant ID, session, run, number of blocks/trials,
    and whether the session is a 'Standard' or 'Practice' set. These parameters are saved
    to a file for future use. If `skip_gui` is True, it loads the last used parameters 
    directly from the file.

    The parameter file used is 'lastParams_PMBR.pickle'.

    Args:
        skip_gui (bool): If True, skip the GUI and use the last saved parameters.

    Returns:
        dict: A dictionary containing the following keys:
            - 'ID' (int): Participant ID (0-100)
            - 'Session' (int): Session number
            - 'Run' (int): Run number
            - 'NbBlocks' (int): Number of experimental blocks
            - 'NbTrials' (int): Number of trials per block
            - 'Set' (str): 'Standard' or 'Practice'
    """
    try:
        param_settings = tools.filetools.fromFile('lastParams_PMBR_.pickle')
    except:
        param_settings = [1,1,1,10,80, 'Standard']
   
    if not skip_gui:
        param_dialog = gui.Dlg('Experimental parameters', pos = [-1200, 100])
        param_dialog.addField('ID (1 to 100)',param_settings[0],tip='Must be numeric only (0 to 100)')
        param_dialog.addField('Session',param_settings[1],tip='Must be numeric only')
        param_dialog.addField('Run',param_settings[2],tip='Must be numeric only')
        param_dialog.addField('Number of blocks',param_settings[3])
        param_dialog.addField('Number of trials',param_settings[4])
        param_dialog.addField('Set', choices=['Standard','Practice'],initial=param_settings[5])
        param_settings=param_dialog.show()

        if param_dialog.OK:
            tools.filetools.toFile('lastParams_PMBR.pickle', param_settings)
            params = {'ID': param_settings[0],
                      'Session': param_settings[1],
                      'Run': param_settings[2],
                      'NbBlocks':param_settings[3],                      
                      'NbTrials':param_settings[4],
                      'Set': param_settings[5]}
        else:
            core.quit()
    else:
        params = {'ID': param_settings[0],
                  'Session': param_settings[1],
                  'Run': param_settings[2],
                  'NbBlocks':param_settings[3],
                  'NbTrials':param_settings[4],
                  'Set': param_settings[5]}
 
    return params



def TI_countdown(window, t):

    """
    Displays a visual countdown timer on the screen for a specified duration, during breaks of before first block.

    The function draws a static circle and a number representing the countdown (in seconds).
    The countdown updates every second and is shown at the specified screen position. 
    If the 'escape' key is pressed during the countdown, the function exits early.

    Args:
        window (psychopy.visual.Window): The PsychoPy window to draw on.
        t (int): Duration of the countdown in seconds.

    Returns:
        int: Returns -1 if the escape key is pressed; otherwise, None.
    """

    clk_text = visual.TextStim(window,text=str(t),pos=(0,0.2),color='black', height=0.07)
    circle = visual.Circle(window, radius=0.1, pos=(0,0.2), fillColor=None, lineColor=[-0.5,-0.5,-0.5], lineWidth=4)

    circle.setAutoDraw(True); clk_text.setAutoDraw(True)
    circle.draw(); clk_text.draw()
    window.flip()
    timer = core.CountdownTimer(t)
    while timer.getTime() > 0:
        if t-timer.getTime() > 1:
            t=t-1
            clk_text.setText(str(t))
            window.flip()
            key = event.getKeys()
            if key and key[0] in ['escape','esc']:
                circle.setAutoDraw(False); clk_text.setAutoDraw(False)
                return -1
    circle.setAutoDraw(False); clk_text.setAutoDraw(False)



def wait_b_pressed(joy, message=None, duration=100, window=None):
    """
    Waits for the participant to press joystick trigger or until a timeout occurs.

    This function monitors the joystick's button input for a given duration (in seconds). 
    If button is pressed, it returns the reaction time (RT) in seconds.
    If the escape key is pressed, it returns -1 to indicate early termination.
    If no button is pressed within the allotted time, the full duration is returned.

    Args:
        joy (joystick.Joystick): The joystick object to monitor.
        message (visual.TextStim, optional): A message to be displayed while waiting.
        duration (float): Maximum waiting time (in seconds).
        window (visual.Window): The PsychoPy window where the message is displayed.

    Returns:
        float: Reaction time in seconds if button is pressed in time.
               Returns -1 if the escape key is pressed.
               Returns the full duration if no input is detected.
    """

    timer = core.CountdownTimer(duration); RT=duration
    
    while timer.getTime()>0:
        if message: message.draw()
        window.flip()
        joy_button_pressed = joy.getButton(0)
        if joy_button_pressed:
            RT = duration - timer.getTime()
            return RT
        # Check for user stop
        key = event.getKeys()
        if key and key[0] in ['escape','esc']:
            return -1
    return RT



def wait_joystick_pushed(joy_r=None,joy_l=None, rect_right_green=None, rect_left_green=None, duration=2, correct_rect=None, rect_left_red=None, rect_right_red=None, joystick_right=None, joystick_left=None, rect_right_black=None, rect_left_black=None):
    """
    Waits for a joystick push (center-out movement) from either the left or right joystick
    within a specified time window and records various data including reaction times and monitored joystick positions.

    It:
    - Detects which joystick was moved.
    - Records reaction times for start and end of movement.
    - Displays visual feedback (colored rectangles) for correct/incorrect responses.
    - Sends triggers based on response accuracy and side.
    - Tracks joystick positions over time for further velocity analysis.

    Visual feedback includes:
        - Green rectangle for correct response.
        - Red rectangle for incorrect response.
        - Black rectangle showing which side is currently correct.

    Args:
        joy_r (visual.ImageStim): Visual stimulus representing the right joystick (for drawing).
        joy_l (visual.ImageStim): Visual stimulus representing the left joystick (for drawing).
        rect_right_green (visual.Rect): Green rectangle for correct right-side response.
        rect_left_green (visual.Rect): Green rectangle for correct left-side response.
        duration (float): Maximum response time allowed (in seconds).
        correct_rect (str): The correct side to respond with ('left' or 'right').
        rect_left_red (visual.Rect): Red rectangle for incorrect left-side response.
        rect_right_red (visual.Rect): Red rectangle for incorrect right-side response.
        joystick_right (joystick.Joystick): Joystick object for the right hand.
        joystick_left (joystick.Joystick): Joystick object for the left hand.
        rect_right_black (visual.Rect): Black rectangle cue indicating right-side is the target.
        rect_left_black (visual.Rect): Black rectangle cue indicating left-side is the target.

    Returns:
        dict or int:
            - A dictionary with the following keys:
                - 'RT_end_right': Reaction time for when right joystick reaches threshold position (90% of y-axis) (if applicable)
                - 'RT_end_left': Reaction time for when left joystick joystick reaches threshold position (90% of y-axis) (if applicable)
                - 'RT_start_right': Time when right joystick started to move
                - 'RT_start_left': Time when left joystick started to move
                - 'right_positions': List of [x, y] positions for right joystick over time
                - 'left_positions': List of [x, y] positions for left joystick over time
                - 'time': List of timestamps corresponding to each joystick position sample
            - Returns -1 if the user presses the Escape key to abort.
    """

    #initiate empty variables
    RT = None
    output = {'RT_end_right': RT, 'RT_end_left': RT, 'RT_start_right': RT, 'RT_start_left': RT,'right_positions':[], 'left_positions':[], 'time':[]}
    right_positions = []
    left_positions = []
    time = []
    timer = core.CountdownTimer(duration)

    flag_RT_start = False

    #get initial joysticks positions
    last_value_right=joystick_right.getY()
    last_value_left=joystick_left.getY()
 

    while timer.getTime()>0: #monitors joysticks positions while the timer doesn't hit the duration limit
        if correct_rect == 'right':
            rect_right_black.draw()
        if correct_rect == 'left':
            rect_left_black.draw()
        if joy_l: joy_l.draw()
        if joy_r: joy_r.draw()

        win.flip() #flipping the window is necessary to update both the screen with new elements and the joysticks position 
        joy_right_y_axis = joystick_right.getY()
        joy_left_y_axis = joystick_left.getY()
        joy_right_x_axis = joystick_right.getX() #x-axis positions are also monitored for velocity analysis
        joy_left_x_axis = joystick_left.getX()
        #print(f'Joy right: {joy_right_y_axis}, Joy left: {joy_left_y_axis}') #for debugging

        # Store RT start if the correct joystick is moved
        if np.abs(joy_right_y_axis - last_value_right) > 0.005 and not flag_RT_start and correct_rect == 'right' :
            output['RT_start_right'] = duration - timer.getTime()
            flag_RT_start = True
        
        if np.abs(joy_left_y_axis - last_value_left) > 0.005 and not flag_RT_start and correct_rect == 'left' :
            output['RT_start_left'] = duration - timer.getTime()
            flag_RT_start = True

        last_value_right = joy_right_y_axis
        last_value_left = joy_left_y_axis

        # stores joysticks positions and time for velocity analysis
        right_positions.append([joy_right_x_axis, joy_right_y_axis])
        left_positions.append([joy_left_x_axis, joy_left_y_axis])
        time.append(timer.getTime())
        

        # right joystick pushed
        if joy_right_y_axis<-0.9: 

            if correct_rect == 'right':
                rect_right_green.autoDraw = True
                RT = duration - timer.getTime()
                send_trigger(7) #correct right answer

            elif correct_rect == 'left':
                rect_left_red.autoDraw = True
                send_trigger(8) #incorrect right answer
            joy_l.draw()
            joy_r.draw()
            win.flip()

            
            # store joystick positions until the end of the timer and update joysticks values
            while timer.getTime()>0:
                joy_right_y_axis = joystick_right.getY()
                joy_left_y_axis = joystick_left.getY()
                joy_right_x_axis = joystick_right.getX()
                joy_left_x_axis = joystick_left.getX()
                right_positions.append([joy_right_x_axis, joy_right_y_axis])
                left_positions.append([joy_left_x_axis, joy_left_y_axis])
                time.append(timer.getTime())
                win.flip()
            
            output['RT_end_right'] = RT
            output['right_positions'] = right_positions
            output['left_positions'] = left_positions
            output['time'] = time

            win.flip()
            rect_right_red.autoDraw = False
            rect_left_red.autoDraw = False
            rect_right_green.autoDraw= False
            rect_left_green.autoDraw = False
            return output
        
        #left joystick pushed
        elif joy_left_y_axis<-0.9:

            if correct_rect == 'right':
                rect_right_red.autoDraw = True
                send_trigger(6) #incorrect left answer

            elif correct_rect == 'left':
                rect_left_green.autoDraw = True
                RT = duration - timer.getTime()
                send_trigger(5) #correct left answer
            joy_l.draw()
            joy_r.draw()
            win.flip()
            while timer.getTime()>0:
                joy_right_y_axis = joystick_right.getY()
                joy_left_y_axis = joystick_left.getY()
                joy_right_x_axis = joystick_right.getX()
                joy_left_x_axis = joystick_left.getX()
                right_positions.append([joy_right_x_axis, joy_right_y_axis])
                left_positions.append([joy_left_x_axis, joy_left_y_axis])
                time.append(timer.getTime())
                win.flip()

            output['RT_end_left'] = RT
            output['right_positions'] = right_positions
            output['left_positions'] = left_positions
            output['time'] = time

            win.flip()
            rect_right_red.autoDraw = False
            rect_left_red.autoDraw = False
            rect_right_green.autoDraw= False
            rect_left_green.autoDraw = False
            return output
        # Check for user stop
        key = event.getKeys()
        if key and key[0] in ['escape','esc']:
            return -1
    return output

def buffer_joystick(joy1, joy2, duration=2):
    """
    Buffers joystick values for a given duration. Useful to avoid the code not updating values between trials.
    Returns a list of joystick positions.
    """
    timer = core.CountdownTimer(duration)
    positions = []
    
    while timer.getTime() > 0:
        axes1 = joy1.getAllAxes()
        axes2 = joy2.getAllAxes()
        positions.append((axes1, axes2))
        win.flip()
        core.wait(0.001)  # Small delay to avoid overwhelming the buffer
    
    return positions


def mouse_clear(mouse):
    mouse.setPos((-10,-10)) # Out of screen



def show_task(params, nTrials=100):
    """
    Main experimental task function.

    This function handles:
        - Display of initial instructions and training blocks (if in practice mode)
        - Initialization of stimuli and joysticks
        - Presentation of each trial: trigger press + joystick movement in 30% of trials
        - Timing and jittering of inter-stimulus intervals
        - Visual and trigger feedback based on participant responses
        - Logging and saving of experimental data
        - End-of-block and end-of-task messaging

    Args:
        params (dict): Dictionary containing experiment parameters, such as:
            - 'ID': Participant ID
            - 'Session': Session number
            - 'Run': Run number
            - 'NbBlocks': Number of blocks in the session
            - 'NbTrials': Number of trials per block
            - 'Set': 'Standard' or 'P' (Practice mode)

        nTrials (int, optional): Total number of trials (overridden if `params['Set'] == 'P'`).

    Returns:
        int:
            - Returns 0 on successful completion of the task.
            - Returns -1 if the participant presses 'esc' to quit the task early.
    
    Task Structure:
        1. **Instructions Phase** - Displays explanation and training prompts.
        2. **Practice Phase** (if selected) - Allows participants to practice both button pressing and joystick movement.
        3. **Main Task Loop** - For each block:
            - Randomly assigns joystick movement trials (left/right or none).
            - Waits for a button press (right joystick trigger).
            - Displays a joystick cue with corresponding enlargement and waits for center-out movement.
            - Sends EEG/parallel port triggers based on participant response and correctness.
            - Collects response times and joystick trajectory data.
        4. **Logging** - Saves all trial/block data to a CSV file if not in practice mode.
        5. **Breaks & Ending** - Displays break message between blocks and thank-you message at the end.

    Notes:
        - The function assumes global variables `win` and `run_path` are defined externally.
        - EEG triggers are sent via the `send_trigger(pin)` function.
        - Joystick movement is captured and interpreted using `wait_joystick_pushed()`.
        - Participant and experimenter can abort the task at any point by pressing the escape button.

    """
    
    global run_path, win
    
    instructions2_0=visual.TextStim(win,text="Joystick Task",pos=(0,0.4),color=(-1,-1,-1),height=0.05,bold=True)
    instructions2_1=visual.TextStim(win,text="Please press the trigger button under your right index finger when you see the message:",pos=(0,0.2),color=(-1,-1,-1),height=0.04)
    instructions2_2=visual.TextStim(win,text="PRESS",pos=(0,0.03),color=(-1,-1,-1),height=0.06,bold=True)
    instructions2_3=visual.TextStim(win,text="On the screen, if the image of a joystick increases in size, push the corresponding joystick forward",pos=(0,-0.2),color=(-1,-1,-1),height=0.04)
    instructions2_4=visual.TextStim(win,text="Try to be as quick and accurate as possible.",pos=(0,-0.3),color=(-1,-1,-1),height=0.04)
    mouse = event.Mouse(visible=False)

    #init joysticks
    joy1 = joystick.Joystick(0)
    joy2 = joystick.Joystick(1)

    # ISI cross
    isi_cross = visual.TextStim(win,text="+",pos=(0,0.05),color=(-1,-1,-1),height=0.2,bold=True)

    #Joytick images
    joy_r_image_path = os.path.join("Images", "t16_right.png")
    joy_r_image = visual.ImageStim(win, image=joy_r_image_path, pos=(0.55,0.07))
    joy_l_image_path = os.path.join("Images", "t16_left.png")
    joy_l_image = visual.ImageStim(win, image=joy_l_image_path, pos=(-0.55,0.07))

    #Press message
    press_message=visual.TextStim(win,text="PRESS",pos=(0,0.05),color=(-1,-1,-1),height=0.05,bold=True)

    #Correct rectangles
    rect_right_green = visual.Rect(win, width=0.65, height=0.75, pos=(0.55,0.07), lineColor='green', lineWidth=4, fillColor = None)
    rect_left_green = visual.Rect(win, width=0.65, height=0.75, pos=(-0.55,0.07), lineColor='green', lineWidth=4, fillColor = None)
    rect_right_red = visual.Rect(win, width=0.65, height=0.75, pos=(0.55,0.07), lineColor='red', lineWidth=4,  fillColor = None)
    rect_left_red = visual.Rect(win, width=0.65, height=0.75, pos=(-0.55,0.07), lineColor='red', lineWidth=4, fillColor = None)
    rect_right_black = visual.Rect(win, width=0.65, height=0.75, pos=(0.55,0.07), lineColor='black', lineWidth=4, fillColor = None)
    rect_left_black = visual.Rect(win, width=0.65, height=0.75, pos=(-0.55,0.07), lineColor='black', lineWidth=4, fillColor = None)  

    # Press test message definition
    press_test_message = visual.TextStim(win, text="We will now train on the first part of the task.", pos=(0, 0.4), color=(-1, -1, -1), height=0.05, bold=False)
    press_test_message2 = visual.TextStim(win, text="Please press the trigger button under your right index when you see the message:", pos=(0, 0.2), color=(-1, -1, -1), height=0.04)
    press_test_message3 = visual.TextStim(win, text="PRESS", pos=(0, 0.03), color=(-1, -1, -1), height=0.06, bold=True)
    press_test_message4 = visual.TextStim(win, text="Try to be as fast and accurate as possible.", pos=(0, -0.2), color=(-1, -1, -1), height=0.04)

    
    # Joystick test message definition
    joy_text = visual.TextStim(win, text="Now, we will train on the second part of the task", pos=(0, 0.4), color=(-1, -1, -1), height=0.04)
    joy_text2 = visual.TextStim(win, text="Please push the joystick that increases in size forward", pos=(0, 0.2), color=(-1, -1, -1), height=0.04)
    joy_text3 = visual.TextStim(win, text="If you push the correct joystick, a green rectangle will appear around it and a red rectangle if you push the wrong one.", pos=(0, 0.03), color=(-1, -1, -1), height=0.04)
    joy_text4 = visual.TextStim(win, text="Try to be as fast and accurate as possible.", pos=(0, -0.2), color=(-1, -1, -1), height=0.04)

    # Ready message
    ready_message = visual.TextStim(win, text="We will now start the task, any questions? ", pos=(0, 0.03), color=(-1, -1, -1), height=0.03, bold=True)
    
    # Instructions
    instructions2_0.draw()
    instructions2_1.draw()
    instructions2_2.draw()
    instructions2_3.draw()
    instructions2_4.draw()
    win.flip()   

    # Wait for keyboard input
    key = event.waitKeys(keyList=['space','5','esc','escape'])
    if key and key[0] in ['escape','esc']:
        print('Escape hit - bailing')
        return -1
   
    win.flip()
    mouse_clear(mouse)

    if params['Set'] == 'P': # Practice run

        #press test message
        press_test_message.draw()
        press_test_message2.draw()
        press_test_message3.draw()
        press_test_message4.draw()
        win.flip()
        key = event.waitKeys(keyList=['space','5','esc','escape']) 
        if key and key[0] in ['escape','esc']:
            print('Escape hit - bailing')
            return -1

        # Press message trials
        for i in range(3):

            joy_l_image.autoDraw = True
            joy_r_image.autoDraw = True
            #isi_cross.draw()
            win.flip() # Clear the screen for the ISI
            core.wait(2)
            mouse_clear(mouse)
            key = wait_b_pressed(joy1, press_message, 0.6, win)
            
        
        joy_l_image.autoDraw = False
        joy_r_image.autoDraw = False

        # Joystick test message
        joy_text.draw()
        joy_text2.draw()
        joy_text3.draw()
        joy_text4.draw()
        win.flip()
        key = event.waitKeys(keyList=['space','5','esc','escape'])
        if key and key[0] in ['escape','esc']:
            print('Escaping')
            return -1
        
        
        # Joystick test
        joy_l_image.autoDraw = True
        joy_r_image.autoDraw = True

        for i in range(4):


            win.flip() 
            core.wait(2)

            if i % 2 == 0: 
                joy_r_image.size += (0.2, 0.2)
                output = wait_joystick_pushed(joy_r_image,joy_l_image,rect_right_green,rect_left_green, duration=1, correct_rect='right', rect_left_red=rect_left_red, rect_right_red=rect_right_red, joystick_right=joy1, joystick_left=joy2, rect_left_black=rect_left_black, rect_right_black=rect_right_black)
                joy_r_image.size -= (0.2, 0.2)
                win.flip() 

                joy_l_image.draw()
                joy_r_image.draw()
                win.flip()  

            elif i % 2 == 1:
                joy_l_image.size += (0.2, 0.2)
                output = wait_joystick_pushed(joy_r_image,joy_l_image,rect_right_green,rect_left_green, duration=1, correct_rect='left', rect_left_red=rect_left_red, rect_right_red=rect_right_red, joystick_right=joy1, joystick_left=joy2, rect_left_black=rect_left_black, rect_right_black=rect_right_black)
                joy_l_image.size -= (0.2, 0.2)
                win.flip() 

                joy_l_image.draw()
                joy_r_image.draw()
                win.flip()


        joy_l_image.autoDraw = False
        joy_r_image.autoDraw = False

        # Ready message
        ready_message.draw()
        win.flip()
        key = event.waitKeys(keyList=['space','5','esc','escape'])
        if key and key[0] in ['escape','esc']:
            print('Escaping')
            return -1


    win.flip()
    mouse_clear(mouse)

    
    log = dict.fromkeys(('ID','Session','Run','Trial'))
    local_timer = core.MonotonicClock()

    
    nb_blocks = params['NbBlocks']
    if params['Set'] == 'P':
        nb_blocks = 1
    nb_trials = params['NbTrials']
    if params['Set'] == 'P':
        nb_trials = 10

    #define percentage of trials for joystick movement
    percentage_joystick = 0.3 #30%
    
    #Indices joysticks
    nb_movements = int(nb_trials*percentage_joystick) #Define the number of total joystick center-out movements
    Nb_right = int(nb_movements/2) # Defines the number of right joystick movements (half the total)

    idcs=np.array(random.sample(range(0,nb_trials), nb_movements)) #Defines the trials where the joystick will be moved
    idx_right=random.sample(range(nb_movements),Nb_right) # Defines the indices of the trials where the right joystick will be moved
    idx_left=np.delete(idcs,idx_right) # Defines the indices of the trials where the left joystick will be moved

    mask=np.zeros(len(idcs),bool)
    mask[idx_right]=True
    idx_right=idcs[mask] # trials where the right joystick will be moved (this method was chosen to avoid selecting the same index for both sides)

    right_positions = []
    left_positions = []
    RT_end_right = 0
    RT_end_left = 0
    RT_start_right = 0
    RT_start_left = 0

    send_trigger(pin=2) #start stimulation


    TI_countdown(win, t=5) # Ramp-up period

    win.flip()
    mouse_clear(mouse)


    
    for block in range(nb_blocks):
        log['Block'] = block + 1
        RTs = []
        
        # Ensure all blocks are the same duration by uniformally distributing the jitters
        jitters_1 = np.linspace(0.65, 0.85, nb_trials)
        jitters1shuffled = np.random.permutation(jitters_1)
        jitters_1 = [round(i, 2) for i in jitters1shuffled]
        jitters_2 = np.linspace(1, 2, nb_trials)
        jitters2shuffled = np.random.permutation(jitters_2)
        jitters_2 = [round(i, 2) for i in jitters2shuffled]
        send_trigger(9) #block start

        for trial in range(nb_trials):
            
            RT_press=0
            RT_end_right = 0
            RT_end_left = 0
            RT_start_right = 0
            RT_start_left = 0
            time=0
            joy_l_image.autoDraw = True
            joy_r_image.autoDraw = True
            win.flip()

            t1=local_timer.getTime()
            log['TrialStart'] = t1
            core.wait(1) # Wait for 1 second before the press message

            press_message.draw()
            win.flip() 
            mouse_clear(mouse)
            RT_press = wait_b_pressed(joy1, press_message, 0.6, win) # Press message, wait for trigger button press, self paced but lasts for max 0.6s

            #TI-EEG trigger
            #send_trigger(pin=2)


            # User hit escape
            if RT_press == -1:
                print('Escape hit - bailing')
                return -1
        
            if RT_press > 0.05: # We have a response

                win.flip() 
                joy_l_image.draw()
                joy_r_image.draw()
                win.flip() 
                

                if RT_press == 1:
                    send_trigger(pin=4) # No response
                else:
                    send_trigger(pin=2) # Response
                    #send_trigger(pin=3)
                    
                isi = jitters_1[trial] # Get the jitter for this trial 
                core.wait(isi) # Wait for ~0.75 seconds before the joystick push


                # trial where right joystick will be pushed
                if trial in idx_right: 
                    
                    joy_r_image.size += (0.15, 0.15) #enlarge the right joystick
                    joy_r_image.draw()
                    joy_l_image.draw()
                    rect_right_black.draw()
                    win.flip()
                    output = wait_joystick_pushed(
                        joy_r_image,joy_l_image,rect_right_green,rect_left_green,1, 
                        correct_rect='right', rect_left_red=rect_left_red, rect_right_red=rect_right_red,
                          joystick_right=joy1, joystick_left=joy2, rect_left_black=rect_left_black, rect_right_black=rect_right_black) # wait for joystick push, lasts 1 seconds
                   
                    
                    RT_end_right = output['RT_end_right']
                    RT_end_left = output['RT_end_left']
                    right_positions = output['right_positions']
                    left_positions = output['left_positions']
                    RT_start_right = output['RT_start_right']
                    RT_start_left = output['RT_start_left']
                    time = output['time']
                    
                    joy_r_image.size -= (0.15, 0.15)
                    win.flip() # Clear the screen for the ISI
                    joy_l_image.draw()
                    joy_r_image.draw()
                    win.flip()  


                # trial where left joystick will be pushed
                elif trial in idx_left:  

                    joy_l_image.size += (0.15, 0.15) #enlarge the left joystick
                    joy_l_image.draw()
                    joy_r_image.draw()
                    rect_left_black.draw()
                    win.flip()
                    output = wait_joystick_pushed(
                        joy_r_image,joy_l_image,rect_right_green,rect_left_green,1, 
                        correct_rect='left', rect_left_red=rect_left_red, rect_right_red=rect_right_red, 
                        joystick_right=joy1, joystick_left=joy2, rect_left_black=rect_left_black, rect_right_black=rect_right_black) # wait for joystick push, lasts 1 seconds
                    
                    
                    RT_end_right = output['RT_end_right']
                    RT_end_left = output['RT_end_left']
                    right_positions = output['right_positions']
                    left_positions = output['left_positions']
                    RT_start_right = output['RT_start_right']
                    RT_start_left = output['RT_start_left']
                    time = output['time']
                    if RT_start_left is not None:
                        RTs += [RT_start_left] # Store RT value to show at the end of the block (we show only the left to avoid potential unlinding/bias from the stimulation, which will target right hand movements)                 
                    
                    joy_l_image.size -= (0.15, 0.15)
                    win.flip() 
                    joy_l_image.draw()
                    joy_r_image.draw()
                    win.flip()

                else:
                    buffer=buffer_joystick(joy1, joy2, duration=1) #Buffer to refresh joystick values, lasts 1 seconds
                    win.flip()

                
                isi2 = jitters_2[trial] # Get the jitter for this trial
                buffer_joystick(joy1, joy2, duration=isi2) # Buffer to refresh joystick values, lasts ~1.5s
                win.flip()

                log['RT_press'] = RT_press
                log['RT_start_right'] = RT_start_right
                log['RT_start_left'] = RT_start_left
                log['RT_end_right'] = RT_end_right
                log['RT_end_left'] = RT_end_left
                log['right_positions'] = right_positions
                log['left_positions'] = left_positions
                log['time'] = time

            else:
                log['RT_press'] = 'NA'
                log['RT_end_right'] = 'NA'
                log['RT_end_left'] = 'NA'
                log['RT_start_right'] = 'NA'
                log['RT_start_left'] = 'NA'
                log['right_positions'] = 'NA'
                log['left_positions'] = 'NA'
                log['time'] = 'NA'


            
            key = event.getKeys()
            if key and key[0] in ['escape','esc']:
                print('Escape hit - bailing')
                return -1

        
            # Save trial data
            log['ID'] = params['ID']
            log['Session'] = params['Session']
            log['Run'] = params['Run']
            log['Trial'] = trial+1
            log['Block'] = block + 1


            # Save if not practice run
            if params['Set'] != 'P':
                # See if run file already exist
                if os.path.exists(run_path):
                    new_file = 0 # Append to file
                else:
                    new_file = 1 # Create new file

                with open(run_path, 'a+') as f:
                    w = csv.DictWriter(f, log.keys(),lineterminator = '\n')
                    if new_file == 1:
                        w.writeheader()
                    w.writerow(log)      
        

        joy_l_image.autoDraw = False
        joy_r_image.autoDraw = False
        send_trigger(3) #end of block
        RT_message=visual.TextStim(win,text=f"Average Reaction Time: {np.round(np.nanmean(RTs),3)}",pos=(0,0),color=(-1,-1,-1),height=0.05,bold=True)
        win.flip()
        RT_message.draw()
        win.flip()
        core.wait(5)
        # Break period
        if block < nb_blocks - 1: # If not the last block
            
            break_message = visual.TextStim(win, text="BREAK", pos=(0, 0), color=(-1, -1, -1), height=0.05, bold=True)
            break_message.autoDraw = True

            TI_countdown(win, t=25) # Break period
            break_message.autoDraw = False
            win.flip()

    # End of task
    if params['Set'] != 'P':
        end_message = visual.TextStim(win, text="End of task. Thank you for your participation!", pos=(0, 0), color=(-1, -1, -1), height=0.05, bold=True)
        end_message.draw()
        win.flip()
        core.wait(5)  # Wait for 5 seconds before closing
    

    return 0
 
    
    
# ------------------------------------------------------------------------    
# Main routine


params = get_parameters()

params['Randomization'] = 1234
if params['Set'] == 'Standard':
    params['Set'] = '1'
elif params['Set'] == 'Practice':
    params['Set'] = 'P'

# Set our random seed
if params['Randomization'] == -1:
    seed = params['ID']
elif params['Randomization']==0:
    seed = None
else:
    seed = params['Randomization']
np.random.seed(seed)

params['TimeStarted'] = str(datetime.now())

### Creating task parameters log file
subject_path = 'Data\\Subject_'+str(params['ID'])
params_path = subject_path+'\\S_'+str(params['ID'])+'_PMBR_task_params.csv'
run_path = subject_path+'\\S_'+str(params['ID'])+'_PMBR_runs.csv'
subject_path = Path(subject_path); 
params_path = Path(params_path); 
run_path = Path(run_path); 

# Create subject path if there isn't one
if not os.path.exists(subject_path):
    os.makedirs(subject_path)

# See if task files already exist
if os.path.exists(params_path):
    new_file = 0 # Append to file
else:
    new_file = 1 # Create new file

with open(params_path, 'a+') as f:
    w = csv.DictWriter(f, params.keys(),lineterminator = '\n')
    if new_file == 1:
        w.writeheader()
    w.writerow(params)


#create window
win = visual.Window(fullscr=True,monitor='testMonitor',screen=1,units="height",color=[-0.5,-0.5,-0.5])
print(f"RefreshRate: {win.getActualFrameRate()} Hz")


#run the task
show_task(params)

win.close()  
core.quit()
