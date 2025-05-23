# Copyright 2024 NVIDIA CORPORATION & AFFILIATES
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
# This file is modified from https://github.com/haotian-liu/LLaVA/

import os
from unittest import mock
import sys

from llava.train.sequence_parallel.monkey_patch import (
    __init__,
    _flash_attention_forward,
    _upad_input,
    flash_attn_varlen_func_helper,
    hybrid_attn_varlen_func_helper,
    new_decoder_forward,
    new_llamamodel_forward,
)
from llava.train.train import train
from llava.train.transformer_normalize_monkey_patch import patched_normalize

# from llava.train.sequence_parallel.grad_ckpt import unsloth_gradient_checkpointing_enable


def __len__(self):
    return len(self.batch_sampler)


def __iter__(self):
    return self.batch_sampler.__iter__()


if __name__ == "__main__":

    with (
        # mock.patch("deepspeed.utils.groups._create_zero_param_parallel_group", new=_create_zero_param_parallel_group_vila),
        mock.patch("transformers.models.llama.modeling_llama.LlamaModel.forward", new=new_llamamodel_forward),
        mock.patch("transformers.models.llama.modeling_llama.LlamaFlashAttention2._upad_input", new=_upad_input),
        mock.patch("transformers.models.llama.modeling_llama.LlamaFlashAttention2.__init__", new=__init__),
        mock.patch(
            "transformers.models.llama.modeling_llama.LlamaFlashAttention2._flash_attention_forward",
            new=_flash_attention_forward,
        ),
        # Ulysses SP patch
        mock.patch(
            "transformers.models.llama.modeling_llama.LlamaFlashAttention2.flash_attn_varlen_func_helper",
            new=flash_attn_varlen_func_helper,
        ),
        # Hybrid SP patch
        mock.patch(
            "transformers.models.llama.modeling_llama.LlamaFlashAttention2.hybrid_attn_varlen_func_helper",
            new=hybrid_attn_varlen_func_helper,
        ),
        mock.patch("transformers.image_processing_utils.normalize", new=patched_normalize),
        mock.patch("accelerate.data_loader.BatchSamplerShard.__len__", new=__len__),
        mock.patch("accelerate.data_loader.BatchSamplerShard.__iter__", new=__iter__),
    ):
        train()
