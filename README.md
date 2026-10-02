---
title: cpt-agent-plugins
description: Personal plugin marketplace for GitHub Copilot in VS Code and Copilot CLI, with plugins in the Agent Plugins 1.0 format.
---

## Overview

This repository is a plugin marketplace. Each folder under [plugins/](plugins) is a
self-contained [Agent Plugins 1.0](https://agent-plugins.org/) package that you install
separately. Install only the plugins a machine needs, and enable or disable them per
workspace.

## Plugins

| Plugin | Skills | Purpose |
|---|---|---|
| [jupyter-notebooks](plugins/jupyter-notebooks) | [create-bash-notebook](plugins/jupyter-notebooks/skills/create-bash-notebook/SKILL.md) | Create Jupyter notebooks on a Bash kernel from a Python environment, with `shellscript` code cells, on Linux, macOS, and Windows (WSL) |

## Install in VS Code

1. Set `chat.plugins.enabled` to `true`.
2. Add the marketplace to your user `settings.json`:

   ```json
   "chat.plugins.marketplaces": [
     "cpinotossi/cpt-agent-plugins"
   ]
   ```

3. Open the Extensions view, search for `@agentPlugins`, and select **Install** on the
   plugins you want.

With Remote SSH, Remote Tunnels, or WSL, Copilot runs on the remote host. Install the
plugins once per remote target.

## Use

Copilot loads a skill automatically when your request matches its description. To
invoke a skill explicitly, type `/` in chat and pick it. Plugin skills carry the plugin
name as prefix, for example:

```text
/jupyter-notebooks:create-bash-notebook notebooks/setup.ipynb with cells for az login
```

## Update a Plugin

1. Change the plugin and bump `version` in its `plugin.json` and in
   [marketplace.json](.github/plugin/marketplace.json).
2. Push to `main`.
3. On each machine run **Extensions: Check for Extension Updates**, or wait for the
   automatic check every 24 hours.

## Add a Plugin or Skill

* New plugin: create `plugins/<plugin-name>/plugin.json` and add an entry with
  `"source": "./plugins/<plugin-name>"` to [marketplace.json](.github/plugin/marketplace.json).
* New skill: create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.
* Name plugins after their domain, not their content type: `jupyter-notebooks`, not
  `jupyter-notebook-tools`. A plugin can hold skills, MCP servers, agents, and hooks.
* Plugin and skill names use lowercase letters, digits, and single hyphens, at most 64
  characters. The skill `name` must equal its folder name; VS Code silently skips skills
  that break this rule.
* Keep scripts inside the skill folder and reference them with paths relative to it.

## License

[MIT](LICENSE)
