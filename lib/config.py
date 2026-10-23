# -*- coding: utf-8 -*-
"""站点构建配置：所有路径与外部地址集中在这里，模板与正文禁写死域名。"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env(key, default):
    v = os.environ.get(key)
    return v if v not in (None, "") else default


SITE_URL = _env("SITE_URL", "https://sotaex.github.io").rstrip("/")
BASE_PATH = _env("BASE_PATH", "/antinel-site").rstrip("/")
if BASE_PATH == "/":
    BASE_PATH = ""

SITE_NAME = "Antinel 监理"
SITE_NAME_EN = "Antinel Steward"
FINGERPRINT = "sha256:b71e570c30ebcbf7"
LICENSE_CODE = "Apache-2.0"
LICENSE_TEXT = "CC-BY-SA-4.0"
LICENSE_DATA = "CC-BY-4.0"

DIR_DATA = os.path.join(ROOT, "data")
DIR_SOURCES = os.path.join(DIR_DATA, "sources")
DIR_CONTENT = os.path.join(ROOT, "content")
DIR_TEMPLATES = os.path.join(ROOT, "templates")
DIR_PARTIALS = os.path.join(ROOT, "partials")
DIR_ASSETS = os.path.join(ROOT, "assets")
DIR_OUT = _env("SITE_OUT", os.path.join(ROOT, "site-output"))

# 真源仓（仅 --refresh-sources 时使用；CI 里不存在）
SRC_REPO = _env("ANTINEL_SRC", r"D:\psl\poc\antinel-security")


def abs_url(path=""):
    """站内路径 → 绝对地址。path 以 / 开头。"""
    p = path if path.startswith("/") else "/" + path
    return SITE_URL + BASE_PATH + p


def link(path=""):
    """站内路径 → 站点内可点击链接（带 BASE_PATH）。"""
    p = path if path.startswith("/") else "/" + path
    return (BASE_PATH + p) or "/"
