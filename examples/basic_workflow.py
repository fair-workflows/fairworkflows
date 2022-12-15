from fairworkflows import FairWorkflow, is_fairstep, is_fairworkflow

print("📋️ Running basic workflow example in examples/basic_workflow.py")

@is_fairstep(label='Addition')
def add(a:float, b:float) -> float:
    """Adding up numbers."""
    return a + b

@is_fairstep(label='Subtraction')
def sub(a: float, b: float) -> float:
    """Subtracting numbers."""
    return a - b

@is_fairstep(label='Multiplication')
def mul(a: float, b: float) -> float:
    """Multiplying numbers."""
    return a * b

@is_fairstep(label='A strange step with little use')
def weird(a: float, b:float) -> float:
    """A weird function"""
    return a * 2 + b * 4


@is_fairworkflow(label='My Workflow')
def my_workflow(in1, in2, in3):
    """
    A simple addition, subtraction, multiplication workflow
    """
    t1 = add(in1, in2)  # 5
    t2 = sub(in1, in2)  # -3
    t3 = weird(t1, in3)  # 10 + 12 = 22
    t4 = mul(t3, t2)  # 22 * -3 = 66
    return t4


fw = FairWorkflow.from_function(my_workflow)

result, prov = fw.execute(1, 4, 3)
print("prov")
print(prov)
# When unpublished it generates URI starting with http://www.example.org/unpublished


prov.publish_as_nanopub(use_test_server=True)

print("FairWorkflow:")
print(fw)
print("PROV:")
print(prov._rdf.serialize(format="trig"))

for step_prov in prov:
    print("STEP PROV")
    print(step_prov)
