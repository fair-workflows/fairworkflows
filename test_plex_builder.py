from fairworkflows import Nanopub, FairStep, FairWorkflow
import rdflib

workflow = FairWorkflow('A test workflow.')
print(workflow)

step_uri = rdflib.URIRef('http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4#step')
np_uri = 'http://purl.org/np/RANBLu3UN2ngnjY5Hzrn7S5GpqFdz8_BBy92bDlt991X4'
np = Nanopub.fetch(np_uri)

step_rdf = rdflib.Graph()
step_rdf += np.assertion.triples((step_uri, None, None))
print(step_rdf)
print(step_rdf.serialize(format='trig').decode('utf-8'))

step1 = FairStep(step_rdf = step_rdf, uri=step_uri)

step1.validate()

step1.is_pplan_step()

step1.description()

step1.is_manual_task()

step1.is_script_task()

step1.rdf

workflow.set_first_step(step1)
print(workflow)

step2 = FairStep(uri=rdflib.term.URIRef('http://www.step.org'))
print(step2)

workflow.add(step1, follows=step2)


print(workflow)

for a in workflow:
    print(a)
