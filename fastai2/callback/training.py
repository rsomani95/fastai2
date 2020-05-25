# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/nbs/18a_callback.training.ipynb (unless otherwise specified).

__all__ = ['ShortEpochCallback', 'GradientAccumulation', 'set_bn_eval', 'BnFreeze', 'bn_types']

# Cell
from ..basics import *
from .progress import *
from .fp16 import *

# Cell
@log_args
class ShortEpochCallback(Callback):
    "Fit just `pct` of an epoch, then stop"
    def __init__(self,pct=0.01,short_valid=True): self.pct,self.short_valid = pct,short_valid
    def after_batch(self):
        if self.iter/self.n_iter < self.pct: return
        if self.training:    raise CancelTrainException
        if self.short_valid: raise CancelValidException

# Cell
@log_args
class GradientAccumulation(Callback):
    "Accumulate gradients before updating weights"
    toward_end,run_before=True,MixedPrecision

    def __init__(self, n_acc=32): store_attr(self, 'n_acc')
    def begin_fit(self): self.count=0

    def after_backward(self):
        self.count += find_bs(self.learn.yb)
        if self.count < self.n_acc: raise CancelBatchException() #skip weight update
        else: self.count=0

    _docs = dict(begin_fit="Set counter to 0",
                 after_backward="Skip weight update if we have not seen enough items")

# Cell
bn_types = (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)

def set_bn_eval(m:nn.Module)->None:
    "Set bn layers in eval mode for all recursive children of `m`."
    for l in m.children():
        if isinstance(l, bn_types) and not next(l.parameters()).requires_grad:
            l.eval()
        set_bn_eval(l)

class BnFreeze(Callback):
    "Freeze moving average statistics in all non-trainable batchnorm layers."
    def begin_batch(self):
        set_bn_eval(self.model)