import os
import pathlib 
import sys
import anndata as an
import torch 
import argparse 
import random 

from os.path import join, dirname, abspath
sys.path.append(join(dirname(abspath(__file__)), '..', 'src'))

import anndata as an 
import sys, os 
sys.path.append('../src')

import sys
import os
import pathlib 
from typing import *

import torch
import numpy as np 
import pandas as pd 
import anndata as an

import pytorch_lightning as pl
from pytorch_lightning.loggers import WandbLogger

from data import *
from lightning_train import *
from model import *
from torchmetrics.functional import *
from networking import download 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        required=False,
    )

    parser.add_argument(
        '--test',
        action='store_true',
        required=False,
    )

    parser.add_argument(
        '--prop',
        type=float,
        default=0.5,
        help='Proportion of dataset to use in ablation',
    )

    device = ('cuda:0' if torch.cuda.is_available() else None)

    args = parser.parse_args()
    name, test, prop = args.name, args.test, args.prop

    here = pathlib.Path(__file__).parent.resolve()
    data_path = join(here, '..', 'data', 'benchmark')

    print('Making data folder')
    os.makedirs(data_path, exist_ok=True)

    for file in ['human_labels_clean.csv', 'human.h5ad']:
        print(f'Downloading {file}')

        if not os.path.isfile(join(data_path, file)):
            download(
                remote_name=join('jlehrer', 'human_benchmark', file),
                file_name=join(data_path, file),
            )

    size = pd.read_csv(join(data_path, 'human_labels_clean.csv')).shape[0]
    sample = int(prop * size)
    sample = random.sample(range(0, size), sample)

    module = DataModule(
        datafiles=[join(data_path, 'human.h5ad')],
        labelfiles=[join(data_path, 'human_labels_clean.csv')],
        class_label='subclass_label',
        sep=',',
        batch_size=64,
        index_col='cell',
        num_workers=32,
        deterministic=True,
        normalize=True,
        assume_numeric_label=False,
        subset=sample,
        stratify=False,
    )

    wandb_logger = WandbLogger(
        project=f"Ablation Study, Unstratified",
        name=f"Proportion={prop}",
    )

    lr_callback = pl.callbacks.LearningRateMonitor(logging_interval='epoch')

    upload_callback = UploadCallback(
        path='checkpoints',
        desc='human_cortical'
    )
    
    early_stopping_callback = pl.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=50,
    )

    trainer = pl.Trainer(
        gpus=(1 if torch.cuda.is_available() else 0),
        auto_lr_find=False,
        logger=wandb_logger,
        max_epochs=500,
        gradient_clip_val=0.5,
        callbacks=[
            lr_callback, 
            upload_callback,
            early_stopping_callback,
        ]
    )

    if not test:
        module.prepare_data()
        module.setup()

        model = SIMSClassifier(
            input_dim=module.num_features,
            output_dim=module.num_labels,
            weights=module.weights,
        )

        trainer.fit(model, datamodule=module)
        trainer.test(model, datamodule=module)
    else:
        raise NotImplementedError("No checkpoints downloaded yet")