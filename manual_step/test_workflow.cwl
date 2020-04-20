#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow
inputs:
  manual_mode: string
outputs:
  final_answer:
    outputSource: manual/results_uri
    type: string
steps:
  manual:
    run: manual.cwl
    in:
      mode: manual_mode
    out:
    - results_uri
