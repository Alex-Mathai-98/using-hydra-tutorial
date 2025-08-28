from omegaconf import DictConfig, OmegaConf
import logging
import os
import json
from datetime import datetime
import hydra

##############################
# setting up loggging
logger = logging.getLogger(__name__)


@hydra.main(version_base="1.1",
    config_path="config",
    config_name="default_config")
def train(
        cfg: DictConfig
    ) :
    """
        Main training function with Hydra configuration management.
    """

    # log the current working directory
    logger.info(f"Working directory : {os.getcwd()}")
    logger.info(f"Experiment name : {cfg.experiment.name}")

    # saving the full config file
    with open("full_config.yaml", "w") as f :
        OmegaConf.save(cfg, f)


    # Create a short experiment summary for easy reference
    experiment_summary = {
        "name": cfg.experiment.name,
        "model": cfg.model.base_model,
        "dataset": cfg.dataset.dataset_name,
        "lr": cfg.hyperparam.lr,
        "batch_size": cfg.hyperparam.batch_size,
        "timestamp": datetime.now().isoformat(),
    }
    
    with open("experiment_info.json", "w") as f:
        json.dump(experiment_summary, f, indent=2)
  
    # Now, write the rest of your experiments
    # using the rest of the config values.
    # For example ::
    # define the model, 
    # the optimizer, 
    # the learning rate
    # the number of epochss


if __name__ == "__main__":
    train()
