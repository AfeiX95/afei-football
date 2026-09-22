# -*- coding: utf-8 -*-
"""gate.py — 一次跑完四道闸门, 只输出紧凑结论(省 token 用)

用法:
  python gate.py <稿件.md> [<稿件.md> ...]
  python gate.py --full <稿件.md>      # 需要看细则时才加 --full

为什么: 原来每篇要分别跑 4 个脚本、各自打印 15-25 行, 一个稿子读 60-100 行输出。
本工具把四道闸门收成"每篇 2-3 行", 只在失败时展开失败项。
平台自动判定: 文件名含"公众号" → 公众号口径(最严); 否则头条口径。
"""
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, args):
    p = subprocess.run([PY, os.path.join(HERE, script)] + args, capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace')


def one(path, full=False):
    name = os.path.basename(path)
    gzh = '公众号' in name
    plat = ['--platform', 'gzh'] if gzh else ['--toutiao']
    ok = True
    fails = []

    # 1+2. 发布闸门
    rc1, o1 = run('risk_scan.py', plat + [path])
    rc2, o2 = run('check_md_release.py', [path] + ([] if gzh else ['--toutiao']))
    # 3. AI 分
    rc3, o3 = run('zhuque_local_check.py', ['--file', path])
    # 4. 盲区层
    rc4, o4 = run('risk_audit.py', [path])

    for rc, o, tag in ((rc1, o1, 'risk_scan'), (rc2, o2, 'md'), (rc3, o3, 'zhuque'), (rc4, o4, 'audit')):
        if rc != 0:
            ok = False
            for ln in o.split('\n'):
                if ln.strip().startswith(('❌', '- ', '⚠')) and '上限' not in ln:
                    fails.append('%s: %s' % (tag, ln.strip()[:78]))

    def g(pat, o, d='—'):
        m = re.search(pat, o)
        return m.group(1) if m else d

    z = g(r'全文均值:\s*([\d.]+)/10', o3)
    ch = g(r'章节数:\s*(\d+)', o2)
    lg = g(r'长句\s*(\d+)\s*个', o2)
    ti = g(r'标题\s*(\d+)\s*字', o2)
    ln = g(r'长句\s*(\d+)\s*个', o2)
    pd = g(r'纯数据句占比\s+(\d+)%', o1)
    cc = g(r'篇幅\s+全字符\s+(\d+)', o1)
    unit = '章节 %s · λ表 %s · 长句 %s · 标题 %s字' % (
        ch, '有' if 'λ±10% 区间表: 有' in o2 else '**无**', lg, ti)
    print('%s %s [%s] 朱雀 %s | 全字符 %s · 纯数据句 %s%% | %s'
          % ('✅' if ok else '❌', name, 'gzh' if gzh else 'tt', z, cc, pd, unit))
    if full:
        print('   risk_scan总体:', g(r'总体:\s*(.*)', o1))
        if fails:
            print('   失败项:')
            for f in fails[:8]:
                print('     ', f)
    elif fails:
        for f in fails[:6]:
            print('     ', f)
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    full = '--full' in a
    files = [x for x in a if x != '--full']
    if not files:
        print(__doc__)
        sys.exit(2)
    allok = all(one(f, full) for f in files)
    sys.exit(0 if allok else 1)
