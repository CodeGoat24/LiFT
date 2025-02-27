#!/bin/bash
export MODEL_PATH="THUDM/CogVideoX-2b"
export CACHE_PATH="~/.cache"
export DATASET_PATH="./dataset"
export OUTPUT_PATH="./checkpoints/CogVideoX-LiFT"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

# if you are not using wth 8 gus, change `accelerate_config_machine_single.yaml` num_processes as your gpu number
accelerate launch --config_file accelerate_config_machine_single.yaml --multi_gpu \
 train.py \
  --gradient_checkpointing \
  --pretrained_model_name_or_path $MODEL_PATH \
  --cache_dir $CACHE_PATH \
  --enable_tiling \
  --enable_slicing \
  --instance_data_root $DATASET_PATH \
  --data_json 'data.json+real_data_openvid' \
  --validation_prompt 'A musician sits on a wooden porch, strumming his acoustic guitar under a starlit sky. The moon casts a soft, silvery glow, illuminating his focused expression and the gentle movements of his hands. The serene night is filled with the melodic sounds of his music, blending harmoniously with the rustling leaves and distant cricket chirps. His attire, a simple white shirt and dark jeans, adds to the tranquil scene, capturing a moment of pure, heartfelt serenade.' \
  --validation_prompt_separator ::: \
  --num_validation_videos 1 \
  --validation_epochs 1 \
  --seed 42 \
  --mixed_precision bf16 \
  --output_dir $OUTPUT_PATH \
  --height 480 \
  --width 720 \
  --fps 8 \
  --max_num_frames 49 \
  --skip_frames_start 0 \
  --skip_frames_end 0 \
  --train_batch_size 8 \
  --num_train_epochs 20 \
  --checkpointing_steps 500 \
  --gradient_accumulation_steps 1 \
  --learning_rate 1e-5 \
  --lr_scheduler cosine_with_restarts \
  --lr_warmup_steps 200 \
  --lr_num_cycles 1 \
  --gradient_checkpointing \
  --optimizer AdamW \
  --adam_beta1 0.9 \
  --adam_beta2 0.95 \
  --max_grad_norm 1.0 \
  --allow_tf32  