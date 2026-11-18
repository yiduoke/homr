# Learning curves of the resolution runs

Training loss = mean over 100 steps as logged; evaluation on the validation list at the end of each epoch.

- A7: 67 training points up to epoch 2.00, 2 evaluation points (/Users/yiduoke/Documents/homr/run/eval_run1/res_logs/run3_ctrl_s7.1.log)
- A11: 67 training points up to epoch 2.00, 2 evaluation points (/Users/yiduoke/Documents/homr/run/eval_run1/res_logs/run3_ctrl_s11.1.log)
- B7: 67 training points up to epoch 2.00, 2 evaluation points (/Users/yiduoke/Documents/homr/run/eval_run1/res_logs/res_B_s7.1.log)
- B11: 38 training points up to epoch 1.13, 1 evaluation points (/Users/yiduoke/Documents/homr/run/eval_run1/res_logs/res_B_s11.1.log)

## Training loss per quarter of the run (mean of the logged points)

| seed | arm | Q1 | Q2 | Q3 | Q4 | last point at epoch |
|---|---|---|---|---|---|---|
| 7 | A | 0.9845 | 0.9642 | 0.9518 | 0.9498 | 2.00 |
| 7 | B | 0.9984 | 0.9672 | 0.9531 | 0.9503 | 2.00 |
| 7 | B - A | +0.0139 | +0.0030 | +0.0013 | +0.0006 | |
| 11 | A | 0.9828 | 0.9644 | 0.9521 | 0.9489 | 2.00 |
| 11 | B | 0.9970 | 0.9669 | 0.9571 | n/a | 1.13 |
| 11 | B - A | +0.0142 | +0.0025 | +0.0050 | n/a | |

## Trend at the cutoff: slope of the training loss over the last half epoch (per epoch, +- 1 s.e.)

| seed | arm | points | slope per epoch | gap B - A: slope per epoch (matched steps) |
|---|---|---|---|---|
| 7 | A | 17 | -0.0015 +- 0.0041 |  |
| 7 | B | 17 | +0.0010 +- 0.0040 | +0.0025 +- 0.0022 |
| 11 | A | 17 | +0.0020 +- 0.0049 |  |
| 11 | B | 18 | -0.0276 +- 0.0060 | -0.0034 +- 0.0022 |

## Evaluation points

| seed | arm | epoch | eval loss | eval accuracy | rhythm acc | pitch acc | position acc |
|---|---|---|---|---|---|---|---|
| 7 | A | 1 | 0.9361 | 0.99863 | 0.99811 | 0.99895 | 0.99708 |
| 7 | A | 2 | 0.9326 | 0.99867 | 0.99821 | 0.99900 | 0.99710 |
| 7 | B | 1 | 0.9371 | 0.99856 | 0.99793 | 0.99895 | 0.99684 |
| 7 | B | 2 | 0.9330 | 0.99865 | 0.99813 | 0.99901 | 0.99703 |
| 11 | A | 1 | 0.9359 | 0.99866 | 0.99814 | 0.99901 | 0.99698 |
| 11 | A | 2 | 0.9326 | 0.99868 | 0.99818 | 0.99904 | 0.99708 |
| 11 | B | 1 | 0.9370 | 0.99855 | 0.99807 | 0.99888 | 0.99675 |

Change from epoch 1 to epoch 2 (negative eval loss / positive accuracy = still improving):

| seed | arm | d eval loss | d eval accuracy |
|---|---|---|---|
| 7 | A | -0.0035 | +0.00004 |
| 7 | B | -0.0042 | +0.00009 |
| 11 | A | -0.0033 | +0.00002 |
