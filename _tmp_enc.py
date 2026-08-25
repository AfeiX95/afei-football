# -*- coding: utf-8 -*-
import sys

fname = sys.argv[1]
raw = open(fname, 'rb').read()

for enc in ['utf-8', 'gbk', 'gb18030']:
    try:
        s = raw.decode(enc)
        print(enc, 'OK, 柏太阳神 in text:', '柏太阳神' in s, '| 长崎 in text:', '长崎' in s)
    except Exception as e:
        print(enc, 'FAIL', e)
