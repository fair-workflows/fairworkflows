from .fairworkflow import FairWorkflow, FairStep


# 1. Create a new (empty) workflow
fw = FairWorkflow(name='add_and_multiply_workflow')



# 2. Define some steps

@FairStep(fw)
def add(dog, cat):
    """
        Add two integers together (int1 and int2).
    """
    result = dog + cat
    return result

@FairStep(fw)
def mult(walrus, bird):
    """
        Multiply two integers together (int1 and int2).
    """
    result = walrus * bird
    return result



# 3. Construct the workflow
input1 = 3
input2 = 5
output1 = add(input1, input2)
output2 = mult(output1, input2)

# 4. Execute the workflow
print("Executing workflow:")
result = fw.execute()
print("Result:", result)

# 5. Publish the workflow and all its steps
fw.nanopublish()
