[English](README.md) · [Türkçe](README.tr.md)

![A warm burgundy orchestra stage with a conductor and distinct helper musicians](docs/assets/cover-en.svg)

# Ustam

<!-- ustam-hub-quickstart:start -->
## Start with Ustam 1.0.0-beta.2

The same local application for Codex, Claude Code, and OpenCode.

**Mac status:** The published beta.1/beta.2 Mac downloads have unresolved first-launch issues. A locally built app was verified on one Mac; this does not establish that the public download opens. beta.3 is not published. See [the Mac notes](docs/ustam-hub.md).

1. **Download:** Open the [beta release](https://github.com/metapak/ustam-opencode-orchestrator/releases/tag/ustam-v1.0.0-beta.2) and extract the Windows/Linux native ZIP completely: [Windows](https://github.com/metapak/ustam-opencode-orchestrator/releases/download/ustam-v1.0.0-beta.2/ustam-1.0.0-beta.2-windows-x86_64.zip) · [Linux](https://github.com/metapak/ustam-opencode-orchestrator/releases/download/ustam-v1.0.0-beta.2/ustam-1.0.0-beta.2-linux-x86_64.zip).
2. **Open:** Open **Ustam.exe** on Windows or **Ustam** on Linux. For a locally built Mac app, open **Ustam.app**. The Mac app contains its runtime and can be moved on its own; keep the extracted Windows/Linux files together. No external Python is required.
3. **Select apps:** Choose Codex, Claude Code, or OpenCode. Install and sign in to each selected provider's CLI.
4. **Add projects:** Add folders inside the local browser page, choose an orchestra, check changes, and apply them.

This beta is unsigned and not notarized. Mac Gatekeeper may block the download. Provider accounts and model access are separate requirements. [Local hub guide](docs/ustam-hub.md).
<!-- ustam-hub-quickstart:end -->

## Projects and orchestras

Add a project, select the provider you use there, then choose a saved orchestra or create one in that project's setup area. Review models and roles before saving. A saved orchestra is reusable configuration; saving it does not start a provider job. Review proposed project changes before applying them.

Configuration and previews can work offline. Starting real work requires the selected provider's CLI, login and model access. Team settings and the runtime's actual execution limits are separate; the page reports those limits. Usage/history describes recorded work, not a live orchestra animation.

## Advanced compatibility

The older provider-specific console remains available for existing projects. Its screenshots, ten-task presets and launchers are described separately in the [legacy reference](docs/legacy-console.md). Follow the [unified app guide](docs/ustam-hub.md) for current setup.

## License

[Apache-2.0](LICENSE) · [Attribution](NOTICE). This is an unofficial community project, not endorsed by provider maintainers.
