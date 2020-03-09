from fairworkflow import FairWorkflow, FairStep

fw = FairWorkflow(name='add_and_multiply_workflow')

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






# Execute workflow

input1 = 3
input2 = 5

output1 = add(input1, input2)

output2 = mult(output1, input2)

print("metadata:\n")
print(fw)

print("Executing workflow:")
result = fw.execute()

print("Result:", result)
