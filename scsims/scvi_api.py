import pathlib
from typing import Union

import anndata as an
import pytorch_lightning as pl

from scsims.lightning_train import DataModule
from scsims.model import SIMSClassifier

here = pathlib.Path(__file__).parent.absolute()


class SIMS:
    def __init__(
        self,
        datafiles: Union[list[str], list[an.AnnData]],
        *args,
        **kwargs,
    ) -> None:
        self.datamodule = DataModule(
            datafiles=[datafiles] if isinstance(datafiles, an.AnnData) else datafiles, 
            # since datamodule expects a list of data always
            *args,
            **kwargs,
        )

        for att, value in self.datamodule.__dict__.items():
            setattr(self, att, value)

    def setup_model(self, *args, **kwargs):
        self._model = SIMSClassifier(self.datamodule.input_dim, self.datamodule.output_dim, *args, **kwargs)

    def setup_trainer(self, *args, **kwargs):
        self._trainer = pl.Trainer(*args, **kwargs)

    def train(self, *args, **kwargs):
        if not hasattr(self, "_trainer"):
            self.setup_trainer(*args, **kwargs)
        if not hasattr(self, "_model"):
            self.setup_model(*args, **kwargs)

        self._trainer.fit(self._model, datamodule=self.datamodule)

    def predict(self, datafiles: an.AnnData, *args, **kwargs):
        results = self._model.predict(datafiles, *args, **kwargs)
        results = results.apply(lambda x: self.label_encoder(x))

        return results

    def explain(self, datafiles: an.AnnData, *args, **kwargs):
        results = self._model.explain(datafiles, *args, **kwargs)
        
        return results