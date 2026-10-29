# -*- coding: utf-8 -*-
"""真源装载。

两种模式：
1. refresh()：从产品仓取一份「随站快照」+ 锁（只在开发机跑，CI 不跑）。
2. load()：只读快照并校验锁。CI 与本地构建走这条，不需要产品仓。

为什么要快照：GitHub Actions 里没有产品仓。但「拷一份进站」= 第二处副本，
会静默落后。所以快照必须带 sha256 锁，构建时校验；锁对不上就红。
"""
import ast
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

from . import config as C

TRUTH = os.path.join(C.DIR_SOURCES, "truth.json")
RULES_COPY = os.path.join(C.DIR_SOURCES, "rules.default.json")


class TruthError(RuntimeError):
    pass


def _sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _sha256_file(p):
    with open(p, "rb") as f:
        return _sha256_bytes(f.read())


def refresh():
    """从产品仓重取快照。返回摘要 dict。"""
    src = C.SRC_REPO
    if not os.path.isdir(src):
        raise TruthError("产品仓不存在：%s（用 --src 或环境变量 ANTINEL_SRC 指定）" % src)
    rp = os.path.join(src, "rules", "default.json")
    if not os.path.isfile(rp):
        raise TruthError("缺真源：%s" % rp)

    raw = open(rp, "rb").read()
    rules_doc = json.loads(raw.decode("utf-8"))
    rules = rules_doc["rules"]

    # 产品常量：单子进程 import，避免多进程被宿主硬杀
    probe = (
        "import json,sys\n"
        "sys.path.insert(0, %r)\n"
        "import antinel as A\n"
        "print(json.dumps({'VERSION':A.VERSION,'VERDICTS':A.VERDICTS,"
        "'EVIDENCE_MEANING':A.EVIDENCE_MEANING}, ensure_ascii=False))\n" % src
    )
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                         text=True, encoding="utf-8", timeout=180)
    if out.returncode != 0:
        raise TruthError("import antinel 失败：%s" % (out.stderr or "")[-500:])
    const = json.loads(out.stdout.strip().splitlines()[-1])

    # 宿主登记：只认 *.json（目录里有 .trash 残留，不能数文件个数）
    hosts, hosts_files = [], []
    hd = os.path.join(src, "rules", "hosts")
    for fn in sorted(os.listdir(hd)):
        if not fn.endswith(".json"):
            continue
        hosts_files.append(fn)
        d = json.load(open(os.path.join(hd, fn), encoding="utf-8"))
        hosts.append({
            "key": d.get("host") or fn[:-5],
            "name": d.get("name") or fn[:-5],
            "vendor": d.get("vendor") or "",
            "tier": d.get("tier") or "",
            "roots": d.get("roots") or [],
            "evidence_count": len(d.get("evidence") or []),
        })

    # 随包自证：从 SKILL.md 的 metadata 里解析，不手抄
    selfproof = {"assertions": None, "assertions_total": None,
                 "digests": None, "digests_total": None, "raw": ""}
    sk = os.path.join(src, "SKILL.md")
    if os.path.isfile(sk):
        txt = open(sk, encoding="utf-8").read()
        m = re.search(r'psl-verified-evidence:\s*"([^"]+)"', txt)
        if m:
            selfproof["raw"] = m.group(1)
            a = re.search(r"assertions\s+(\d+)\s*/\s*(\d+)", m.group(1))
            dg = re.search(r"(\d+)\s*/\s*(\d+)\s+digests", m.group(1))
            if a:
                selfproof["assertions"] = int(a.group(1))
                selfproof["assertions_total"] = int(a.group(2))
            if dg:
                selfproof["digests"] = int(dg.group(1))
                selfproof["digests_total"] = int(dg.group(2))

    truth = {
        "schema": "antinel-truth/1",
        "captured_at": _now(),
        "src_path": src,
        "product_version": const["VERSION"],
        "rules_version": rules_doc.get("version"),
        "rules_description": rules_doc.get("description", ""),
        "rules_sha256": _sha256_bytes(raw),
        "gates": rules_doc.get("gates", {}),
        "category_order": rules_doc.get("category_order", []),
        "rules": rules,
        "verdicts": const["VERDICTS"],
        "evidence_meaning": const["EVIDENCE_MEANING"],
        "hosts": hosts,
        "hosts_files": hosts_files,
        "selfproof": selfproof,
        "measured": measure(src),
    }

    os.makedirs(C.DIR_SOURCES, exist_ok=True)
    with open(RULES_COPY, "wb") as f:
        f.write(raw)  # 逐字节拷贝，J-13 要求与真源一致
    with open(TRUTH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(truth, f, ensure_ascii=False, indent=2)
    return {"version": truth["product_version"], "rules": len(rules),
            "hosts": len(hosts), "sha256": truth["rules_sha256"][:16]}


def _now():
    import datetime
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


# ---------------------------------------------------------------- 实测
# 为什么要有这一段：F-004 / F-005 / F-006 曾经是三个写死在 gen.py 里的字面量，
# evidence 指向 README 或 THREAT_MODEL.md —— 那是「文档这么说」，不是「我们量过」。
# 两者在页面上长得一模一样，读者无从分辨。现在这三条改成在 --refresh-sources
# 时真取一次数，取不到就报错，不静默沿用上一版的值。
#
# 三条各自的取数方式不同，快照里逐条写明，页面上也逐条写明：
#   F-004 本机实测（真的跑钩子进程，取中位数）
#   F-005 静态扫描（import 面）＋ 声明（常驻与联网，来自安装代码路径）
#   F-006 源码解析（从计分实现的源码里抓权重）
# 混在一起说成「实测」是不诚实的，所以 measured 里带 method 字段。

def _measure_hook_latency(src, n=5):
    """真跑钩子，测端到端时延。**结果不作为事实页的数字**，只进快照备查。

    ★ 为什么不当事实：这台机器上量出来的数随 cwd 形状剧烈变化。
      临时目录不是 git 仓库，钩子会走一条超时路径，端到端 3 秒上下；
      而产品文档写的是 65 毫秒。两个数都不是假的，量的是两件事。
      把一个夹具形状下的读数写进「事实清单」，等于用一个可疑数替换
      另一个可疑数——那正是本站纪律里「夹具合成形状」那一族。
      所以：实测值留在快照里给维护者看，事实页对读者标「声明，未复测」。

    ★ 隔离：产品钩子会把审计写进 cwd/.psl 与中枢目录。这里把
      USERPROFILE / HOME / ANTINEL_HUB_DIR 全指到临时目录，跑完丢掉。
    """
    hook = os.path.join(src, "hooks", "pre_tool_use.py")
    if not os.path.isfile(hook):
        raise TruthError("缺钩子入口，没法测时延：%s" % hook)
    payload = json.dumps({"tool_name": "Bash",
                          "tool_input": {"command": "ls"}}).encode("utf-8")
    td = tempfile.mkdtemp(prefix="sitemeasure_")
    try:
        work = os.path.join(td, "proj")
        home = os.path.join(td, "home")
        os.makedirs(work)
        os.makedirs(home)
        env = {k: v for k, v in os.environ.items()
               if k not in ("PYTHONPATH", "PYTHONHOME")}
        env.update({"USERPROFILE": home, "HOME": home,
                    "ANTINEL_HUB_DIR": os.path.join(home, ".antinel"),
                    "TMP": td, "TEMP": td, "TMPDIR": td})
        samples = []
        for _ in range(n):
            t0 = time.perf_counter()
            p = subprocess.run([sys.executable, "-E", "-X", "utf8", hook],
                               input=payload, capture_output=True,
                               cwd=work, env=env, timeout=120)
            samples.append((time.perf_counter() - t0) * 1000.0)
            if p.returncode not in (0, 2):
                raise TruthError("钩子测量跑挂了（rc=%s）：%s"
                                 % (p.returncode,
                                    (p.stderr or b"")[-300:].decode("utf-8", "replace")))
        med = statistics.median(samples)
        return {
            "p50_ms": int(round(med)),
            "n": n,
            "min_ms": int(round(min(samples))),
            "max_ms": int(round(max(samples))),
            "platform": sys.platform,
            "at": _now(),
            "usable_as_fact": False,
            "why_not": "cwd 是临时目录（非 git 仓），触发的是产品的超时路径，"
                       "不是用户机器上的形状",
            "method": "子进程冷启动 %d 次取中位数；隔离家目录与中枢" % n,
        }
    finally:
        shutil.rmtree(td, ignore_errors=True)


#: 扫描面：只扫发布件里的运行时目录。ci/ 与 tests/ 会 import pytest 之类，
#: 那不是运行时依赖，扫进来会把 stdlib_only 判成「否」。
_RUNTIME_DIRS = ("hooks", "psl", "scripts", "tools")


def _measure_stdlib(src):
    """扫运行时代码的 import，列出非标准库模块。

    用 ast 而不是正则：正则会把注释里的 `import requests` 也算进去，
    也会漏掉 `from x import (a,\\n b)` 这种跨行写法。

    ★ 扫描面必须显式列举，不能用 os.walk(仓根)。第一次跑就是这么错的：
      进了 output/ 与 changelog/，撞上一个带 BOM 的临时脚本当场炸。
      而 BOM 本身不是缺陷——`utf-8-sig` 读得进来。
    """
    stdlib = getattr(sys, "stdlib_module_names", None)
    if not stdlib:
        raise TruthError("这个解释器没有 sys.stdlib_module_names，量不了标准库面")
    dirs = [os.path.join(src, d) for d in _RUNTIME_DIRS]
    dirs = [d for d in dirs if os.path.isdir(d)]
    tops = sorted(os.path.join(src, f) for f in os.listdir(src)
                  if f.endswith(".py") and os.path.isfile(os.path.join(src, f)))
    files = list(tops)
    for d in dirs:
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", ".psl", "build",
                                        "dist", "node_modules")]
            files += [os.path.join(dirpath, f) for f in filenames if f.endswith(".py")]
    # 本仓自己的模块：**整仓**的模块名都算本地，但只收名字、不解析文件。
    # 第一版只收扫描面里的名字，于是 `import inbox_guards`（文件在 ci/，
    # 不在运行面里）被当成外部依赖，判成「标准库面不干净」——
    # 量出来的错误比没量更糟：它会让页面写出一个假的依赖名。
    local = set()
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".worktrees", "__pycache__", ".psl",
                                    "build", "dist", "node_modules", "output",
                                    "site-output")]
        local |= {f[:-3] for f in filenames if f.endswith(".py")}
        local |= set(dirnames)
    externals, scanned = set(), 0
    for p in files:
        try:
            tree = ast.parse(open(p, encoding="utf-8-sig").read())
        except (SyntaxError, UnicodeDecodeError) as e:
            raise TruthError("解析不了 %s：%s" % (p, e))
        scanned += 1
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:              # 相对导入，本仓自己的
                    continue
                mods = [(node.module or "").split(".")[0]]
            else:
                continue
            for m in mods:
                if m and m not in stdlib and m not in local:
                    externals.add(m)
    return {
        "stdlib_only": "是" if not externals else "否",
        "externals": sorted(externals),
        "files_scanned": scanned,
        "dirs": [os.path.basename(d) for d in dirs],
        "at": _now(),
        "method": "ast 解析运行时代码的 import，比对 sys.stdlib_module_names",
    }


def _measure_scoring(src):
    """从计分实现的源码里抓权重。抓不到就报错，不猜。"""
    p = os.path.join(src, "scripts", "report.py")
    if not os.path.isfile(p):
        raise TruthError("缺计分实现，没法解析权重：%s" % p)
    txt = open(p, encoding="utf-8").read()
    m = re.search(r'100\s*-\s*(\d+)\s*\*\s*summary\.get\(\s*"critical"[^)]*\)'
                  r'\s*-\s*(\d+)\s*\*\s*summary\.get\(\s*"warning"', txt)
    if not m:
        raise TruthError("计分公式的形状变了，解析不到权重：%s" % p)
    return {
        "critical_weight": int(m.group(1)),
        "warning_weight": int(m.group(2)),
        "source": "scripts/report.py",
        "line": txt[:m.start()].count("\n") + 1,
        "at": _now(),
        "method": "正则解析计分实现的源码",
    }


def measure(src):
    """三条：时延、标准库面、计分权重。任何一条取不到都抛错。"""
    return {
        "hook_latency": _measure_hook_latency(src),
        "stdlib": _measure_stdlib(src),
        "scoring": _measure_scoring(src),
    }


def load():
    """读快照并校验。任何不一致都抛 TruthError（构建失败），不回退旧值。"""
    if not os.path.isfile(TRUTH):
        raise TruthError("缺快照 %s —— 先跑 python gen.py --refresh-sources" % TRUTH)
    truth = json.load(open(TRUTH, encoding="utf-8"))
    if not os.path.isfile(RULES_COPY):
        raise TruthError("缺规则快照 %s" % RULES_COPY)

    actual = _sha256_file(RULES_COPY)
    if actual != truth["rules_sha256"]:
        raise TruthError(
            "规则快照被改过：锁里是 %s，实际 %s。若是故意更新真源，跑 --refresh-sources"
            % (truth["rules_sha256"][:16], actual[:16]))

    # 快照内部的版本三方一致性（rules 文件版本 / import 到的版本 / 自证里记的版本）
    vs = {truth.get("rules_version"), truth.get("product_version")}
    if len({v for v in vs if v}) != 1:
        raise TruthError("快照内版本不一致：rules=%s product=%s"
                         % (truth.get("rules_version"), truth.get("product_version")))

    # 宿主数：只认解析成功的 *.json
    if len(truth["hosts"]) != len({h["key"] for h in truth["hosts"]}):
        raise TruthError("宿主登记里有重复 key")
    return truth
