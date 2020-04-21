# FAIRWorkbench
Modules for implementation of the FAIR Workbench.

# Prerequisites
The np scripts needs to be called to generate rsa keys in the `~/.nanopub` directory.

```shell script
./np mkkeys -d RSA
```


## How to run FAIR workbench
The cli interface can be run as follows:

```python workflow-cli.py generate-workflow```

You will then be prompted for the required information, after which your workflow skeleton will be generated.

If you just want to see what the output looks like, you can run:

```python generate_sample_workflow.py```

This will generate a sample workflow with one step, and place the result in the folder `sample_output/`.
