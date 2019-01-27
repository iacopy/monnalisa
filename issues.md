## Issue 1
Crash found:
```
Running 2 islands across 5 processes
Improvements/total = 3/1,000 (0.3%)
Island 77eb3af run: 13.86 (72.18 it/s)
Improvements/total = 16/1,000 (1.6%)
Island 9153a5b run: 15.85 (63.08 it/s)
Islands run_speed: 124.193 it/s
#0 - i0 it: 261,000, gl: 8,900, v = 39,669,029 (-43,541)
#1 - i1 it: 261,000, gl: 8,900, v = 45,021,981 (-91,078)
Variab gen (mean) = 2244.000
f1: 0
f2: 0
Traceback (most recent call last):
  File "src/monnalisa.py", line 238, in <module>
    main(opts)
  File "src/monnalisa.py", line 200, in main
    if new_best_ev_offspring['evaluation'] < best_ev_offspring['evaluation']:
TypeError: 'NoneType' object is not subscriptable
```