# using-hydra-tutorial
A tutorial to understand how to use the hydra config management for ML projects


### Directory structure
```
config/
├── default_config.yaml
├── model/
│   ├── codesage_v1.yaml
├── dataset/
│   ├── commit_plus_PR_qwen_32B.yaml
└── hyperparam/
    ├── basic_config.yaml
```

### Running the project using `uv` command

`uv run python /home/alex/Desktop/Github-Repos/using-hydra-tutorial/hydra-proj/src/main.py`

Hydra will by default, load the "default_config.yaml" as it's mentioned in the `@hydra.main` decorator.

The default_config.yaml loads all the values from the `defaults` list. If you want to override any of these parameters, you need to do so by over-riding the relevant arguments when running the python file. For example,

`uv run python /home/alex/Desktop/Github-Repos/using-hydra-tutorial/hydra-proj/src/main.py model=codesage_v2`


### Performing a parameter sweep

Here I am varying the learning-rate hyperparameter from `2e-5` to `2e-7` using the `--multirun` argument.

`uv run python /home/alex/Desktop/Github-Repos/using-hydra-tutorial/hydra-proj/src/main.py hyperparam.lr=2e-5,2e-6,2e-7 --multirun`

This will run the experiment multiple times by doing the following.

1. It will load all the config values from the respective folders mentioned in the `defaults` section.
2. It will then override the original learning rate with the different learning rates provided in the command automatically. 


### Keeping track of all the results

1. Dump all the experiment information into an `experiment_info.json` file for each folder.

2. Write a python script that collects all this information and creates a csv file that automatically has all the experiment configurations and their final names. The code `experiment_tracker.py` (by Claude) does this for you. When running the below command, you will see an `experiment_index.csv` file that lists all the experiments with the configuration values.


`uv run python /home/alex/Desktop/Github-Repos/using-hydra-tutorial/hydra-proj/src/experiment_tracker.py "list"`