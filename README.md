# FY27 Territory Plan

A Copilot plugin that turns a SuperDash export into an FY27 territory plan bucketed into
the Innovate, Trust and Scale plays, with Salesforce/Gong engagement enrichment performed
inside your own Copilot session.

## Install

```bash
git clone https://github.com/TheRajeev08/fy27-territory-plan.git \
  ~/.copilot/installed-plugins/fy27-territory-plan
```

Restart the Copilot App, then ask:

> Build my FY27 territory plan from ~/Downloads/Super Summary.xlsx

The plugin itself lives in [`fy27-territory-plan/`](fy27-territory-plan/) — this repo is the
bundle directory the plugin loader scans. See that folder's README for requirements, the
trust model and what the workbook contains.

## No Revenue MCP access?

Use the CRM-free browser app instead:
<https://therajeev08.github.io/fy27-territory-plan-team/>
