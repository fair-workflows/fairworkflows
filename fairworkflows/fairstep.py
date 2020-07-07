import inspect

def fairstep(func):
    """
    Decorator to convert step to an appropriate workflow format (e.g. CWL)
    """


    print(inspect.getfullargspec(func))

    arginfo = inspect.getfullargspec(func) 

    # Check that all variables provided have been given types
    for arg in arginfo.args:
        print("Arg ", arg)
        if arg not in arginfo.annotations:
            raise ValueError(f'Argument {arg} does not have a type annotation.')
        else:
            print(arginfo.annotations[arg])


    # Check that return type is explicitly stated
    if 'return' not in arginfo.annotations:
        raise ValueError(f'Function does not have a return type specified')
    else:
        return_type = arginfo.annotations['return']
        print('Returns:', return_type)

    return func
