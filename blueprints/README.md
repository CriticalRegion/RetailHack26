# NVIDIA retail AI blueprints (reference copies)

Snapshots of NVIDIA's public retail blueprints, for reference and reuse during the hackathon. Each folder is an unmodified copy of the upstream repository at the commit below, without its git history. All four are Apache-2.0 (see each folder's `LICENSE`, `LICENSE-3rd-party.txt` and, where present, `LICENSE-assets.txt`).

| Folder | What it is | Upstream | Commit | Catalog page |
|---|---|---|---|---|
| [`multi-agent-intelligent-warehouse`](multi-agent-intelligent-warehouse/) | Multi-agent warehouse operations assistant | [NVIDIA-AI-Blueprints/multi-agent-intelligent-warehouse](https://github.com/NVIDIA-AI-Blueprints/multi-agent-intelligent-warehouse) | `a6404ed` | [build.nvidia.com](https://build.nvidia.com/nvidia/multi-agent-intelligent-warehouse) |
| [`retail-agentic-commerce`](retail-agentic-commerce/) | Agentic commerce (agent-driven checkout) | [NVIDIA-AI-Blueprints/retail-agentic-commerce](https://github.com/NVIDIA-AI-Blueprints/retail-agentic-commerce) | `83c5f22` | [build.nvidia.com](https://build.nvidia.com/nvidia/retail-agentic-commerce) |
| [`retail-shopping-assistant`](retail-shopping-assistant/) | Multi-agent retail shopping assistant | [NVIDIA-AI-Blueprints/retail-shopping-assistant](https://github.com/NVIDIA-AI-Blueprints/retail-shopping-assistant) | `c20044b` | [build.nvidia.com](https://build.nvidia.com/nvidia/retail-shopping-assistant) |
| [`retail-catalog-enrichment`](retail-catalog-enrichment/) | Product catalog enrichment (text and images) | [NVIDIA-AI-Blueprints/retail-catalog-enrichment](https://github.com/NVIDIA-AI-Blueprints/retail-catalog-enrichment) | `debc251` | [build.nvidia.com](https://build.nvidia.com/nvidia/retail-catalog-enrichment) |

## Related reading (no public code)

- Nebius blog: [Inventory, store operations, and fine-tuning: three NVIDIA retail agent blueprints on Nebius](https://nebius.com/blog/posts/retail-ai-agents-nvidia-blueprints-nebius). It covers the Inventory Lab, Agent Harness for store operations, and an intelligent-warehouse fine-tuning flywheel. These are early access, and the post links no repositories.
- Nebius webinar: [Build production-ready retail store agents with NVIDIA Agent Harness on Nebius](https://nebius.com/events/webinar-production-ready-retail-store-agents).

## Updating a copy

```bash
git clone --depth 1 https://github.com/NVIDIA-AI-Blueprints/<name>.git /tmp/<name>
rsync -a --delete --exclude .git /tmp/<name>/ blueprints/<name>/
```

Then update the commit in the table. Some upstream files sit under `dist/` or other ignored paths, so stage them with `git add -f`.
