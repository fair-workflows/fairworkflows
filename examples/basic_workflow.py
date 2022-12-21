import logging

from fairworkflows import FairWorkflow, is_fairstep, is_fairworkflow

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

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
# When unpublished it generates URI starting with http://www.example.org/unpublished
# Should we change this to the temp nanopub URI?

fw.publish_as_nanopub(use_test_server=True, publish_steps=True)

for step in fw:
    print("STEP FW")
    print(step)

prov.publish_as_nanopub(use_test_server=True)

fw._rdf.serialize(f"examples/basic_workflow.workflow.trig", format="trig")
prov._rdf.serialize(f"examples/basic_workflow.prov.trig", format="trig")

for step_prov in prov:
    print("STEP PROV")
    print(step_prov)


# Not working with nanopubs due to conflict with the graphs using the same namespaces
# def merge_graphs(graph_list):
#     """Merge RDFLib graphs while preserving the contexts"""
#     merged = ConjunctiveGraph()
#     for g in graph_list:
#         for c in g.contexts():
#             for s, p, o, cont in g.quads((None, None, None, c)):
#                 merged.add((s, p, o, c))
#     return merged
# to_merge = [fw._rdf, prov._rdf]
# for step_prov in prov:
#     to_merge.append(step_prov._rdf)
# g = merge_graphs(to_merge)
# g.serialize(f"examples/basic_workflow.trig", format="trig")
