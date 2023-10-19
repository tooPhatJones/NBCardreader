import OLYMPUS

def add_access_hours_to_user_data(user_dict):
    for uid, user_info in user_dict.items():
        if 'access_hours' not in user_info:
            # If access_hours field is missing, add it
            if 'clearance' in user_info:
                clearance = user_info['clearance']
                if clearance == 'level 1':
                    user_info['access_hours'] = '9 AM - 5 PM'
                elif clearance == 'level 2':
                    user_info['access_hours'] = '8 AM - 6 PM'
                elif clearance == 'level 3':
                    user_info['access_hours'] = '7 AM - 7 PM'
                else:
                    user_info['access_hours'] = 'Unknown'
            else:
                user_info['access_hours'] = 'Unknown'

# Example usage:
user_dict = {
    'user1': {
        'name': 'John',
        'age': 30,
    },
    'user2': {
        'name': 'Alice',
        'age': 25,
        'access_hours': '9 AM - 5 PM',
    },
    'user3': {
        'name': 'Bob',
        'age': 35,
    }
}

add_access_hours_to_user_data(user_dict)
OLYMPUS.rewrite_user_dict(user_dict)

# Print updated user_dict
for uid, user_info in user_dict.items():
    print(f'UID: {uid}')
    print(f'User Data: {user_info}')
    print()

