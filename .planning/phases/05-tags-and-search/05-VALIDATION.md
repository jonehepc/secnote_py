---
phase: 05
slug: tags-and-search
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-11
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/python -m pytest tests/ -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/ -q`
- **After every plan wave:** Run `.venv/bin/python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-TBD | TBD | TBD | Phase 05 decisions | TBD | 标签与搜索不写入明文缓存或加密正文 HTML | unit/integration | `.venv/bin/python -m pytest tests/ -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] 为搜索服务、标签编辑、主窗口集成补充或扩展 pytest 测试文件
- [ ] 使用现有 `.venv` 运行 Python 测试，不使用系统 Python

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 标签栏与搜索弹窗交互 | Phase 05 decisions | PySide6 桌面 UI 的视觉和焦点行为需要人工确认 | 启动应用，创建/编辑标签，打开搜索弹窗，验证结果跳转和正文不被置脏 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
