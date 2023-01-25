import pathlib
from os.path import join
from typing import Union

import anndata as an
import numpy as np
import pandas as pd
import pytorch_lightning as pl
import torch

from scsims.lightning_train import DataModule
from scsims.model import SIMSClassifier

here = pathlib.Path(__file__).parent.absolute()


class SIMS:
    def __init__(
        self,
        adata: Union[an.AnnData, list[an.AnnData]],
        labels_key: str,
        verbose=True,
        *args,
        **kwargs,
    ) -> None:
        self.adata = adata
        self.labels_key = labels_key
        self.verbose = verbose

        self.datamodule = DataModule(
            datafiles=[self.adata] if isinstance(self.adata, an.AnnData) else self.adata,  # since datamodule expects a list of data always
            label_key=labels_key,
            class_label=self.labels_key,
            *args,
            **kwargs,
        )

        self.label_encoder = self.datamodule.label_encoder

    def setup_model(self, *args, **kwargs):
        self.model = SIMSClassifier(self.datamodule.input_dim, self.datamodule.output_dim, *args, **kwargs)

    def setup_trainer(self, *args, **kwargs):
        self.trainer = pl.Trainer(
            *args,
            **kwargs,
        )

    def train(self, *args, **kwargs):
        if not hasattr(self, "datamodule"):
            self.setup_data()
        if not hasattr(self, "trainer"):
            self.setup_trainer()
        if not hasattr(self, "model"):
            self.setup_model()

        self.trainer.fit(self.model, datamodule=self.datamodule)

    def predict(self, adata: an.AnnData):
        results = self.model.predict(adata)
        results = results.apply(lambda x: self.label_encoder(x))

        return results
