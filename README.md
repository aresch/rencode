# rencode

The rencode module is similar to bencode from the BitTorrent project.  For complex, heterogeneous data structures with many small elements, r-encodings take up significantly less space than b-encodings:

```
>>> len(rencode.dumps({'a':0, 'b':[1,2], 'c':99}))
13

>>> len(bencode.bencode({'a':0, 'b':[1,2], 'c':99}))
26
```

This version of rencode is a complete rewrite in Cython to attempt to increase the performance over the pure Python module written by Petru Paler, Connelly Barnes et al.


## Performance Comparison
The test program used for these results is included in the repository:
https://github.com/aresch/rencode/blob/master/tests/timetest.py

### Encode functions
```
test_encode_fixed_pos_int:
	rencode.pyx: 0.003s (+0.013s) 589.17%
	rencode.py:  0.016s

test_encode_int_int_size:
	rencode.pyx: 0.006s (+0.032s) 625.99%
	rencode.py:  0.038s

test_encode_int_long_long_size:
	rencode.pyx: 0.014s (+0.026s) 279.96%
	rencode.py:  0.040s

test_encode_int_short_size:
	rencode.pyx: 0.006s (+0.030s) 629.80%
	rencode.py:  0.036s

test_encode_str:
	rencode.pyx: 0.006s (+0.010s) 263.96%
	rencode.py:  0.017s

test_encode_dict:
	rencode.pyx: 0.135s (+0.302s) 324.68%
	rencode.py:  0.437s

test_encode_fixed_list:
	rencode.pyx: 0.012s (+0.025s) 307.78%
	rencode.py:  0.037s

test_encode_fixed_neg_int:
	rencode.pyx: 0.003s (+0.012s) 536.97%
	rencode.py:  0.015s

test_encode_fixed_dict:
	rencode.pyx: 0.046s (+0.105s) 331.07%
	rencode.py:  0.151s

test_encode_int_char_size:
	rencode.pyx: 0.005s (+0.029s) 687.64%
	rencode.py:  0.034s

test_encode_fixed_str:
	rencode.pyx: 0.003s (+0.011s) 438.07%
	rencode.py:  0.015s

test_encode_list:
	rencode.pyx: 0.148s (+0.228s) 253.68%
	rencode.py:  0.376s

test_encode_none:
	rencode.pyx: 0.004s (+0.011s) 386.06%
	rencode.py:  0.014s

test_encode_int_big_number:
	rencode.pyx: 0.011s (+0.019s) 264.32%
	rencode.py:  0.030s

test_encode_float_64bit:
	rencode.pyx: 0.003s (+0.011s) 416.19%
	rencode.py:  0.014s

test_encode_bool:
	rencode.pyx: 0.004s (+0.014s) 447.57%
	rencode.py:  0.018s

test_encode_float_32bit:
	rencode.pyx: 0.003s (+0.010s) 417.86%
	rencode.py:  0.014s

Encode functions totals:
	rencode.pyx: 0.412s (+0.888s) 315.49%
	rencode.py:  1.301s
```
### Decode functions

```
test_decode_fixed_list:
	rencode.pyx: 0.003s (+0.020s) 848.67%
	rencode.py:  0.022s

test_decode_int_long_long_size:
	rencode.pyx: 0.003s (+0.013s) 484.80%
	rencode.py:  0.016s

test_decode_dict:
	rencode.pyx: 0.267s (+0.406s) 251.81%
	rencode.py:  0.673s

test_decode_fixed_dict:
	rencode.pyx: 0.087s (+0.123s) 241.32%
	rencode.py:  0.211s

test_decode_float_32bit:
	rencode.pyx: 0.002s (+0.007s) 536.88%
	rencode.py:  0.009s

test_decode_int_big_number:
	rencode.pyx: 0.007s (+0.010s) 256.05%
	rencode.py:  0.017s

test_decode_int_char_size:
	rencode.pyx: 0.002s (+0.014s) 754.12%
	rencode.py:  0.016s

test_decode_fixed_neg_int:
	rencode.pyx: 0.001s (+0.004s) 389.03%
	rencode.py:  0.006s

test_decode_fixed_str:
	rencode.pyx: 0.009s (+0.009s) 199.78%
	rencode.py:  0.019s

test_decode_float_64bit:
	rencode.pyx: 0.002s (+0.007s) 540.17%
	rencode.py:  0.009s

test_decode_bool:
	rencode.pyx: 0.002s (+0.004s) 369.49%
	rencode.py:  0.006s

test_decode_fixed_pos_int:
	rencode.pyx: 0.002s (+0.004s) 368.96%
	rencode.py:  0.006s

test_decode_list:
	rencode.pyx: 0.019s (+0.247s) 1403.77%
	rencode.py:  0.266s

test_decode_none:
	rencode.pyx: 0.002s (+0.004s) 367.05%
	rencode.py:  0.006s

test_decode_int_short_size:
	rencode.pyx: 0.002s (+0.014s) 716.47%
	rencode.py:  0.016s

test_decode_str:
	rencode.pyx: 0.010s (+0.026s) 364.51%
	rencode.py:  0.036s

test_decode_int_int_size:
	rencode.pyx: 0.002s (+0.014s) 705.92%
	rencode.py:  0.016s

Decode functions totals:
	rencode.pyx: 0.421s (+0.926s) 319.79%
	rencode.py:  1.348s
```

### Overall functions

```
test_overall_encode:
	rencode.pyx: 0.069s (+0.120s) 274.42%
	rencode.py:  0.189s

test_overall_decode:
	rencode.pyx: 0.051s (+0.153s) 400.57%
	rencode.py:  0.204s

Overall functions totals:
	rencode.pyx: 0.120s (+0.273s) 327.98%
	rencode.py:  0.393s
```


## Author
* Andrew Resch <andrewresch@gmail.com>
* Website: https://github.com/aresch/rencode

## License
See [COPYING](https://github.com/aresch/rencode/blob/master/COPYING)  for license information.
