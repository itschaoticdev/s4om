# Security Policy for Sims4 Multiplayer Dev

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security & Protocol Safety

This repository contains development tools, protocol analyzers, and regression test suites for Sims4 multiplayer network synchronization.
- **Network Boundaries:** Test harnesses and launchers run on local loopback (`127.0.0.1`) or user-configured private LAN.
- **Safe Sandboxing:** In-game Python script injections execute strictly within standard sandbox boundaries without privileged system access.

## Reporting a Vulnerability

Please report security issues privately via GitHub Security Advisories or contact `mo9652962-ai@users.noreply.github.com`.
