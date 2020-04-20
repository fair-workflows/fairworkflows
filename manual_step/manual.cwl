#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python3", "-m", "manual.manual"]

inputs:
  mode:
    type: string
    inputBinding:
      position: 1

stdout: cwl.output.json

outputs:
  results_uri:
    type: string
