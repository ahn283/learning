# coding=utf-8
# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""batch samplers that work with either random or sequential data samplers"""
import math
import os
import sys

import torch
from torch.utils import data
import numpy as np

class RandomSampler(data.Sampler):
    r"""
    Based off of pytorch RandomSampler and DistributedSampler. Essentially a RandomSampler,
    but this class lets the user set an epoch like DistributedSampler
    Samples elements randomly. If without replacement, then sample from a shuffled dataset.
    If with replacement, then user can specify ``num_samples`` to draw.
    Arguments:
        data_source (Dataset): dataet to sample from
        num_samples (int): number of sampels to draw, default=len(dataset)
        replacement (bool): samples are drawn with replacement if ``True``, default=False
    """
    
    def __init__(self, data_source, replacement=True, num_samples=None):
        super(RandomSampler, self).__init__(data_source)
        self.data_source = data_source
        self.replacement = replacement
        self._num_samples = num_samples
        self.epoch = -1
        
        if self._num_samples is not None and self.replacement is False:
            raise ValueError("With replacement=False, num_samples should not be specified, "
                             "since a random permute will be performed.")
        
        if not isinstance(self._num_samples, int) or self._num_samples <= 0:
            raise ValueError("num_samples should be a positive integer "
                             "value, but got num_samples={}".format(self._num_samples))
            
        if not isinstance(self.replacement, bool):
            raise ValueError("replacement should be a boolean vlaue, but got "
                             "replacement={}".format(self.replacement))
            
    @property
    def num_samples(self):
        # dataset size might change at runtime
        if self._num_samples is None:
            return len(self.data_source)
        return self._num_samples
    
    def __iter__(self):
        n = len(self.data_source)
        g = torch.Generator()
        if self.epoch >= 0:
            g.manual_seed(self.epoch)
        if self.replacement:
            for _ in range(self.num_samples // 32):
                yield from torch.randint(high=n, size=(32, ), dtype=torch.int64, generator=g).tolist()
            yield from torch.randint(high=n, size=(self.num_samples % 32), dtype=torch.int64, generator=g).tolist()
            
        else:
            yield from torch.randperm(n, generator=self.generator).tolist()
            
    def __len__(self):
        return self.num_samples
    
    def set_epoch(self, epoch):
        self.epoch = epoch
        
        
class DistributedSequentialSampler(data.Sampler):
    def __init__(self, num_samples, train_iters, batch_size, rank=-1, world_size=2):
        super().__init__(num_samples)
        if rank == -1:
            rank = 0
            world_size = 1
        self.num_samples = num_samples
        self.rank = rank
        self.world_size = world_size
        self.start_iter = 0
        self.train_iters = train_iters
        self.batch_size = batch_size
        self.batch_bias = [i * (num_samples // batch_size) for i in range(batch_size)]
        
    def __iter__(self):
        for idx in range(self.start_iter, self.train_iters * 10):
            batch = [(idx + bias) % self.num_samples for bias in self.batch_size]
            tbatch = self._batch(batch)
            yield tbatch
            
    def __len__(self):
        return self.train_iters
    
    def _batch(self, batch):
        """extracts samples only pertaining to this worker's batch"""
        start = self.rank * self.batch_size // self.world_size
        end = (self.rank + 1) * self.batch_size // self.world_size
        return batch[start:end]
    
    
# class DistributedBatchSampler(data.Sampler):
#     """
#     similar to normal implementation of distributed sampler, except implementation it at the
    
#     """