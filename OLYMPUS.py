import firebase_admin
from firebase_admin import credentials, db


#TODO test the below imports with an esp
# import board
# import digitalio
# from digitalio import DigitalInOut
# from adafruit_pn532.i2c import PN532_SPI


import time
import json
from datetime import datetime, timedelta
import traceback
import logging, sys

#level = logging.DEBUG
level = logging.INFO
logging.basicConfig(level=level)
logger = logging.getLogger("olympus")
#logger.addHandler(sys.stdout)
# python3 olympus.py --log=debug  # to try different level
logger.debug("logging configured")

import functools
def debug(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__}()")
        result = func(*args, **kwargs)
        return result
    return wrapper

import qrcode

#import custom packages
import Check_Gsheet_UID
import Read_MFRC522
import Get_Buttons
import Pi_to_OLED
#import Doorbot

#https://console.firebase.google.com/u/0/project/noisebridge-rfid-olympus/
#https://www.freecodecamp.org/news/how-to-get-started-with-firebase-using-python/
#https://firebase.google.com/docs/database/security/get-started?hl=en&authuser=2
# Circuit Python port for MFRC522 https://github.com/domdfcoding/circuitpython-mfrc522

#TODO: change firebase rules so that Members can only add guests and memebrs
#TODO: change firebase so guests to only view their experation date

logger.debug("finished imports")


# Add an authorized UID to the database

level_99 = "Gods"
level_3 = "Members"
level_2 = "Associates"
level_1 = "Guests"

#ref.child('Mytikas').child(level_3).set({"uid":"08174ab9"})

# Retrieve authorized UIDs from the database
#authorized_uids = ref.child('Mytikas').get()
#print("Authorized UIDs:", authorized_uids)

local_cache = {}



@debug
def strike_the_door():
    print("Striking the door")
    logger.info("Striking the door")
    Pi_to_OLED.OLED_off(20)
    Pi_to_OLED.New_Message("Striking the door")
    
    
    Get_Buttons.set_pin(20, True)
    time.sleep(5)
    Get_Buttons.set_pin(20, False)


@debug
def uid_is_valid(UID, cache):
    #Check cache if the UID exists, else check the server
    print("Checking Validity")
    logger.info("Checking Validity")
    
    def not_expired(card):
        print("Checking Expiration")
        logger.info("Checking Expiration")
        presentDate = datetime.now()
        present_unix_timestamp = datetime.timestamp(presentDate)*1000
        end_unix_date = card["expire_date"]


        #logger.debug(f"{present_unix_timestamp=} > {end_unix_date=} or {end_unix_date=}")

        logger.debug(f"{card['exp']=} {presentDate=}")
        if present_unix_timestamp < end_unix_date or end_unix_date == 0:
            print(f"Card {UID} Not expired")
            logger.info(f"Card {UID} Not expired")
            return True
        else:
            print(f"Card {UID} Is expired")
            logger.info(f"Card {UID} Is expired")
            return False
            
    
    card = cache.get(UID)
    if card:
        print("Card is found in cache")
        logger.info("Card is found in cache")
        if not_expired(card):
            return True
    else:
        return False
  
@debug
def rewrite_user_dict(users):
    rewrite_json(json.dumps(users))

@debug
def rewrite_json(new_json):
    if not new_json:
        raise ValueError("tried to write nothing")
    logger.debug(f"{new_json=}")
    with open("offline_json.json", "w") as f:
        f.write(new_json)

@debug
def load_json():
    with open("offline_json.json", "r") as f:
        user_dict = json.loads(f.read())
        return user_dict        

@debug
def add_uid(mentor_UID, new_UID, mentor_clearance_level, prodigy_clearance_level, user_dict):
    #Adds a user to the server
    print("Adding User")
    logger.info("Adding User")
    #send_user_message("Adding User")
    #TODO test this part
    current_time = datetime.now()
    current_unix_timestamp = datetime.timestamp(current_time)*1000


    if (mentor_clearance_level == level_2) or (mentor_clearance_level == level_3) or (mentor_clearance_level == level_99):
        if (prodigy_clearance_level == level_3) and (mentor_clearance_level == level_3) or (mentor_clearance_level == level_99):
            # member - unlimited
            new_tag_data = {
                'clearance': prodigy_clearance_level,  # Replace with your actual tag ID
                'expire_date': 0,
                'issue_date': current_unix_timestamp,
                'exp': "NA",
                'iss': str(current_time),
                'UID':new_UID,
                'user_handle':"",
                'mentor': mentor_UID
            }
        elif (prodigy_clearance_level == level_2) and (mentor_clearance_level == level_3) or (mentor_clearance_level == level_99):
            # associate - can only add guests, no expiration
            new_tag_data = {
                'clearance': prodigy_clearance_level,  # Replace with your actual tag ID
                'expire_date': 0,
                'issue_date': current_unix_timestamp,
                'exp': "NA",
                'iss': str(current_time),
                'UID':new_UID,
                'user_handle':"",
                'mentor': mentor_UID
            }
        elif (prodigy_clearance_level == level_1) and (mentor_clearance_level == level_2) or(mentor_clearance_level == level_3) or (mentor_clearance_level == level_99):
            # guest - 30 day exp / daily time limit
            expiration_time = current_time + timedelta(days=30)
            expiration_unix_timestamp = datetime.timestamp(expiration_time)*1000
            new_tag_data = {
                'clearance': prodigy_clearance_level,  # Replace with your actual tag ID
                'expire_date': expiration_unix_timestamp,
                'issue_date': current_unix_timestamp,
                'exp': str(expiration_time),
                'iss': str(current_time),
                'UID':new_UID,
                'user_handle':"",
                'mentor': mentor_UID
            }
        #ref.child('Mytikas').update({new_UID: new_tag_data})
    
        #def func(*args, **kwargs)
        
        new_user = { new_tag_data['UID']: new_tag_data }
        user_dict = dict(user_dict, **new_user)
        rewrite_user_dict(user_dict)
        
        print("Added User", new_UID, "to", prodigy_clearance_level)
        logger.info(f"Added User {new_UID} to {prodigy_clearance_level}")
        return user_dict
    else:
        print("Only associate or big M Members can do this action")
        logger.info("Only associate big M Members can do this action")

@debug
def send_log(log):
    #Inform sever of unauthorized scanning, succesful scanning, and give a time stamp, inform of users added and by whom
    #ref.child('Ourea').push().set(log)
    with open("offline_log_file.txt", "a+") as log_file:
        print(log, file=log_file)

@debug
def read_user_action(switch, button):
    #reads state of buttons to determine whether we are adding a guest or Big M Member
    #TODO test the reading of these buttons
    #TODO investigate the use of https://docs.python.org/3/library/signal.html

    if switch and button:
        return level_3
    elif switch:
        return level_2
    else:
        return level_1       
       
@debug
def look_up_clearance_level(card_uid, cache):
        #formatted_UID = f'"{card_uid}"'

        card = cache.get(card_uid)
        if card:
            clearance = card.get('clearance')
            return clearance
        else:
            print("error card id",card_uid,"returns",card)
            print("cache", cache)
            logger.info("error card id",card_uid,"returns",card)
            logger.info("cache", cache)

@debug
def generate_QR(new_UID):
    
    url = f"https://docs.google.com/forms/d/e/1FAIpQLSdXIPnJPoPdBreH9FOQjW-s5nUuZ4QHThNK59u3kmUDplx3Bg/viewform?usp=pp_url&entry.181306502={new_UID}"
    return



@debug
def main():
    logger.debug("Done caching")
    user_dict = load_json()

    Pi_to_OLED.New_Message("Ready")
    Pi_to_OLED.OLED_off(3)
    
    while True:
        time.sleep(.1)

        card_uid = Read_MFRC522.Read_UID()
        logger.debug(f"{card_uid=}")

        switch, button = Get_Buttons.read()
        
        clearence = look_up_clearance_level(card_uid, user_dict)

        #Doorbot.check_door_status()
        
        is_valid = uid_is_valid(card_uid, user_dict)
        logger.debug(f"{card_uid=} {is_valid=} {switch=}")


        #
        #if not card_uid: continue # nothing there # must've been the wind 

        ## check is valid ()
        #if switch: # adding someone
        #    if is_valid:
        #        # add them!
        #    else:
        #        # try again / not today
        #else: # not switch, normal entry
        #    if is_valid: # welcome
        #    else: # who even are you / expired


        if card_uid and is_valid and not switch:
            print(switch, button)
            logger.info(f"{switch=} {button=}")

            hour_now = datetime.hour
            if (clearence == level_1) and (hour_now > 10) and (hour_now < 22)
                strike_the_door()
            elif (clearence == level_1) and (hour_now < 10) and (hour_now > 22)
                Pi_to_OLED.New_Message("You are outside of access hours")
            else:
                strike_the_door()
            send_log(("Opened door to "+card_uid+" at "+str(datetime.now())))
        
        elif card_uid and is_valid and (switch == True) and ((clearence == level_2) or (clearence == level_3) or (clearence == level_99)):
            #TODO provide some feedback that we are going into a special mode here to add users
            
            Pi_to_OLED.New_Message("SUDO engaged")
            Pi_to_OLED.OLED_off(100)
            time.sleep(1)
            Pi_to_OLED.New_Message("If adding a big M, hold red button. If adding an associate do nothing. For 30 day access flip down switch.")
            time.sleep(5)
            switch, button = Get_Buttons.read()
            prodigy_level = read_user_action(switch,button)
            mentor_clearance = look_up_clearance_level(card_uid, user_dict)
            
            Pi_to_OLED.New_Message("Place new member card now")
            new_UID = Read_MFRC522.Read_UID(30, card_uid)
            
            if new_UID != "":
                user_dict = add_uid(card_uid, new_UID, mentor_clearance, prodigy_level, user_dict)
                send_log(("Added Acess from " + card_uid + " to " + new_UID + " at " + str(datetime.now())))
                Pi_to_OLED.New_Message("New user: Please Scan QR and enter name")
                Pi_to_OLED.New_UID_QR_Image(new_UID)
                time.sleep(20)
                Pi_to_OLED.OLED_off(1)
            else:
                print("Card reading timed out")
                logger.info("Card reading timed out")
                Pi_to_OLED.New_Message("Card reading timed out or clearence")
        
        elif card_uid and is_valid and (switch == True) and (clearence == level_1):
            print("Need Big M to do this")
            logger.info("Need Big M to do this")
            Pi_to_OLED.New_Message("Need Big M to do this, switch off")
            Pi_to_OLED.OLED_off(5)
            time.sleep(2)
        
        elif card_uid:
            print("Access Denied")
            logger.info("Access Denied")
            Pi_to_OLED.New_Message("Access Denied")
            Pi_to_OLED.OLED_off(5)
            time.sleep(5)
            send_log(("Denied Access to " + card_uid + " at "+str(datetime.now())))
        else:
            continue
    
if __name__ == "__main__":
    try:
        print("starting")
        logger.info("starting")
        main()
    except Exception:
        print(traceback.format_exc())
        logger.error(traceback.format_exc())
        main()
