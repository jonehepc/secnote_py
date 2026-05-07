# SecNotepad 项目

## 沟通语言

- 与用户沟通请使用中文
- 供人类阅读的文档（如 PLAN.md、SPEC.md、RESEARCH.md 等）需使用中文撰写
- 代码注释可使用英文或中文，以清晰为准
- GSD 工作流的内部指令、配置文件、代码标识符不受此限制，使用英文

## Git 工作流

- 新 phase 开始前创建对应的 git 分支（由 GSD 配置 `branching_strategy: phase` 自动处理）
- 分支命名格式：`gsd/phase-{N}-{name}`

## gsd:ship 行为

执行 `gsd:ship` 时：
1. 提交当前所有更改
2. 推送到远程仓库（`git push`）
3. 主动提醒用户是否需要创建 PR，以及创建 PR 后的建议操作（如代码审查、合并策略等）

<!-- GSD:project-start source:PROJECT.md -->
## Project

**SecNotepad**

一个本地加密笔记本应用，提供分区树 + 页面列表的层级笔记管理。笔记内容以加密文件形式存储在本地，用户通过密钥打开。富文本编辑、标签和搜索是核心编辑功能。面向需要安全存储笔记的个人用户使用。
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
