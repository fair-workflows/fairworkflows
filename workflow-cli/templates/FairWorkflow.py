from fairworkflow import FairWorkflow, FairStep

{{steps}}

# 1. Create a new (empty) workflow
fw = FairWorkflow(name={{workflow_name}})

# 2. Define some steps


{%for step in steps %}
@FairStep(fw)
def {{step['name']}}():
    """
        {{step['description']}}
    """
    pass
{% endfor %}
