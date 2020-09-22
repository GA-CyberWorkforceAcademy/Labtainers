import os
import requests
import json
import getpass
from cryptography.fernet import Fernet
import base64

course_id = '164'
get_item1 = requests.get('https://gitlab.com/ga-cyberworkforceacademy/labtainer/-/raw/master/item1')
item1 = base64.b64decode(get_item1.content)
item2 = 'MkFuYk4wYjJCX25nbUdULWxCZHBCNktCZmptRklsREVobk5OQVQ4SjV5Zz0='
item2 = item2.encode('utf8')
item2 = base64.b64decode(item2)
f = Fernet(item2)
access_token = f.decrypt(item1).decode('utf8')
working_dir = '/home/{}/labtainer_xfer'.format(getpass.getuser())
auth_header = {'Authorization': 'Bearer {}'.format(access_token)}


def parseUserName():
    # Parse json activity file for username information
    with open(activity_file, 'r') as read_json:
        user_name = json.load(read_json)
    user_name = list(user_name.keys())[0]
    # Clean up output for user email
    user_name = user_name.replace('_at_','@')
    user_name = user_name.split('.', 2)[:1]
    user_email= "".join(user_name)
    return user_email

def getUserID():
    #Query Canvas API endpoint for user ID using user_email
    response = requests.get('https://gacybercenter.instructure.com/api/v1/accounts/self/users?search_term={}'.format(user_email), headers=auth_header)
    user_data = json.loads(response.text)[0]
    user_id = user_data['id']
    return str(user_id)

def getAssignments():
    # Pull assignment data and create dictionary for reference
    get_assignments = requests.get('https://gacybercenter.instructure.com/api/v1/courses/{}/assignments'.format(course_id), headers=auth_header)
    assignment_data = json.loads(get_assignments.text)
    assignment_dict = [d.get('name') for d in assignment_data]
    assignment_dict2 = [d.get('id') for d in assignment_data]
    global assignment_data_dict
    assignment_data_dict = dict(zip(assignment_dict, assignment_dict2))
    return assignment_data_dict

def getAssignmentID():
    # Associate ID with assignment name
    # Parse json activity file for assignment name information
    with open(activity_file, 'r') as read_json:
        activity_name = json.load(read_json)
    activity_name = list(activity_name.keys())[0]
    # Clean up output for user email
    activity_name = activity_name.replace('_at_','@')
    activity_name = activity_name.rsplit('.', 1)[1]
    assignment_id = ""
    if activity_name in assignment_data_dict:
        assignment_id = assignment_data_dict[activity_name]
    return assignment_id, activity_name
  
def gradeAssignment():
    # Parse activity for grade information
    with open(activity_file, 'r') as read_json:
        activity_data = json.load(read_json)
    dict_name = list(activity_data.keys())[0]
    grade_dict = activity_data['{}'.format(dict_name)]['grades']
    if True in grade_dict.values():
        grade_pts = 100
        return grade_pts
    else:
        grade_pts = 0
        return grade_pts

def uploadGrade():
    # Upload grade to Canvas API endpoint
    # Check if grade already exists
        grade_data = 'grade_data[{}][posted_grade]={}'.format(user_id, grade_pts)
        requests.post('https://gacybercenter.instructure.com/api/v1/courses/{}/assignments/{}/submissions/update_grades'.format(course_id, assignment_id), data=grade_data, headers=auth_header)

def checkGradeExists():
    #Check Canvas API endpoint for existing grade data
    get_assignments = requests.get('https://gacybercenter.instructure.com/api/v1/courses/{}/assignments/{}/submissions/{}'.format(course_id, assignment_id, user_id), headers=auth_header)
    graded_data = json.loads(get_assignments.text)
    grade_exists = ''
    grade = graded_data.get('grade')
    if grade == '100':
        grade_exists = True
    else:
        grade_exists = False
    return grade, grade_exists

# Pull current assignments from Canvas and create a dictionary for the values
getAssignments()

# Loop through json files in the assignment directory

try:
    for root, dirs, files in os.walk(working_dir):
        for json_file in files:
            activity_file = os.path.join(root, json_file)
            if activity_file.endswith('.json'):
                # Determine user Email
                user_email = parseUserName()
                # Determine UserID from Canvas API Call
                user_id = getUserID()
                # Determine assignment ID
                assignment_data = getAssignmentID()
                assignment_id = assignment_data[0]
                assignment_name = assignment_data[1]
                # Grade Assignment
                grade_pts = gradeAssignment()
                # Check for existing grade and push grade to assignment data if equal to 100
                grade_query = checkGradeExists()
                grade_exists = grade_query[1]
                grade = grade_query[0]
                if (grade_exists != True) and (grade_pts == 100):
                    uploadGrade()
                    print('{} assignment with a grade of {} submitted!'.format(assignment_name, grade_pts))
                else:
                    print('{} assignment has already been submitted with a grade of {}!'.format(assignment_name, grade))
except:
    print("Exception Occured: No JSON files in student directory or lab naming convention is wrong, nothing to grade")
