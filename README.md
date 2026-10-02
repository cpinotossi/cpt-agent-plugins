---
title: agent-plugins
description: Personal agent skills for GitHub Copilot in VS Code and Copilot CLI, packaged as an Agent Plugins 1.0 plugin.
---

## Overview

This repository is an [Agent Plugins 1.0](https://agent-plugins.org/) package. Install it
once per machine and its skills are available in every project, in VS Code and in
GitHub Copilot CLI.

## Skills

| Skill | Purpose |
|---|---|
| [create-bash-notebook](skills/create-bash-notebook/SKILL.md) | Create Jupyter notebooks on a Bash kernel from a Python environment and keep code cells on `shellscript`, on Linux, macOS, and Windows (WSL) |

## Install in VS Code

1. Set `chat.plugins.enabled` to `true`.
2. Run **Chat: Install Plugin From Source** from the Command Palette.
3. Enter `https://github.com/cpinotossi/agent-plugins`.

With Remote SSH, Remote Tunnels, or WSL, Copilot runs on the remote host. Install the
plugin once per remote target.

To use a local clone instead, register it in `settings.json`:

```json
"chat.pluginLocations": {
  "/path/to/agent-plugins": true
}
```

## Update

1. Change the skill and bump `version` in [plugin.json](plugin.json).
2. Push to `main`.
3. On each machine run **Extensions: Check for Extension Updates**, or wait for the
   automatic check every 24 hours.

## Add a Skill

* Create `skills/<skill-name>/SKILL.md`.
* `name` in the frontmatter must equal the folder name: lowercase letters, digits, and
  single hyphens, at most 64 characters. VS Code silently skips skills that break this
  rule.
* Keep scripts inside the skill folder and reference them with paths relative to it.

## License

[MIT](LICENSE)
