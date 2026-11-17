#!/bin/bash
while true; do
  out=$(ssh -o ConnectTimeout=15 vast-homr4 'ls /workspace/onnx/meter_control/ 2>&1' 2>&1)
  echo "$out" | grep -q "decoder_.*fp16.onnx" && break
  sleep 60
done
sleep 45
ssh vast-homr4 'ls -la /workspace/onnx/meter_control/'
