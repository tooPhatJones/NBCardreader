import OLYMPUS

user_dict = OLYMPUS.load_json()

def update_clearance_level(user_dict):
    for uid, user_info in user_dict.items():
        if 'clearance' in user_info:
            clearance = user_info['clearance']
            if clearance == 'level_2':
                user_info['clearance'] = 'level_3'
            elif clearance == 'level_3':
                user_info['clearance'] = 'level_99'

update_clearance_level(user_dict)
OLYMPUS.rewrite_user_dict(user_dict)

