# -*- coding: utf-8 -*-
"""真源装载。

两种模式：
1. refresh()：从产品仓取一份「随站快照」+ 锁（只在开发机跑，CI 不跑）。
2. load()：只读快照并校验锁。CI 与本地构建走这条，不需要产品仓。

为什么要快照：GitHub Actions 里没有产品仓。但「拷一份进站」= 第二处副本，
会静默落后。所以快照必须带 sha256 锁，构建时校验；锁对不上就红。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

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
    hosts = []
    hd = os.path.join(src, "rules", "hosts")
    for fn in sorted(os.listdir(hd)):
        if not fn.endswith(".json"):
            continue
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
        "selfproof": selfproof,
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
