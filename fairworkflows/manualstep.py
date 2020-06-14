from datetime import datetime

def manualstep(description, completed=False, byWhom=None, remarks=''):
    if completed is False:
        raise ValueError('Manual step has not been registered as completed. Please complete the task, and then set completed=true')
    if byWhom is None:
        raise ValueError('byWhom must be specified. This should be the name of the person who carried out or is signing off on this manual task.')
 
    print('Manual step marked as completed by', byWhom, ' at', datetime.now())
    print('The task description was:\n', description)
    print('Additional remarks provided:\n', remarks)
