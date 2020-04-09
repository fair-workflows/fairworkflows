from .fairworkflow import FairWorkflow, FairStep


# 1. Create a new (empty) workflow
fw = FairWorkflow(name='add_and_multiply_workflow')



# 2. Define some steps

@FairStep(fw)
def add(int1, int2):
    """
        Add two integers together (int1 and int2).
    """
    result = int1 + int2
    return result

@FairStep(fw)
def mult(int1, int2):
    """
        Multiply two integers together (int1 and int2).
    """
    result = int1 * int2
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
