# KMH OIA — Phone-Only Build Setup

Status: CONFIGURATION PROPOSED IN A REVIEW BRANCH; CODESPACE NOT YET CREATED OR RUNTIME-VERIFIED.

## Goal

Use an Android phone and Bluetooth keyboard as the control surface while GitHub Codespaces provides the remote development environment. Keep AWS resources uncreated until the owner sets a monthly budget and approves the estimate.

## What this repository configuration provides

- Python 3.12 development feature.
- VS Code web editor customization with the Python extension.
- A post-create compile check only; no AWS resources, deployments, or paid services are created.
- Three reusable tasks: unit tests, compile check, and read-only deployment preflight.
- No automatic package installation from an unreviewed requirements file.
- No secrets, credentials, AWS keys, or production endpoints are stored in the repository.

## Start from Android

1. Open the repository in Chrome: https://github.com/thuyainminnyo-hub/kmh-oia
2. Open the Code menu and select the Codespaces tab.
3. Select the reviewed branch chore/phone-first-codespaces-setup (or its merged successor) and choose Create codespace.
4. Before confirming, check the machine size and who will be billed. Start with the smallest available machine (normally 2 cores).
5. Open the Codespaces web editor. If the mobile layout hides the Code/Codespaces controls, use Chrome's browser menu and request the desktop site.
6. In the web editor, open Terminal, then New Terminal.
7. Run:
   - python --version
   - python -m compileall -q src tests scripts
   - python -m unittest discover -s tests -v
   - python scripts/deployment_preflight.py
8. Record the exact command, result, timestamp, and Codespace commit SHA in the PR. Do not describe a local Codespaces run as a GitHub Actions result.

## GitHub Codespaces cost controls

- Check the account's included Codespaces quota and the billing owner before creating a Codespace. Personal Free accounts currently include 120 core-hours and 15 GB-month storage; personal Pro accounts include 180 core-hours and 20 GB-month storage. Organization/enterprise accounts do not receive the personal free quota by default.
- A 2-core Codespace consumes 2 core-hours for each wall-clock hour it runs. Stop it as soon as work is complete.
- The default idle timeout is 30 minutes. Set a shorter personal timeout if practical; an active Codespace can still consume compute until it stops.
- Delete unused Codespaces to reduce future storage charges. Deleting one does not reverse storage already accumulated during the current billing period.
- Do not enable prebuilds for this repository during the initial phone-only pilot.
- Do not add a payment method or raise a spending limit without the owner's review.

## Security rules

- Never paste AWS root credentials, access keys, Vercel tokens, GitHub personal access tokens, or private signing keys into chat, issues, source files, or terminal output.
- Do not add .env files or secrets to Git.
- Use GitHub's web authentication flow for Codespaces.
- When AWS is eventually created, enable root MFA, avoid root for daily work, use IAM Identity Center/temporary credentials, and apply least privilege.
- Do not create VPC, NAT Gateway, ALB, ECS, RDS, or other billable AWS resources until the monthly budget and architecture estimate are approved.
- Keep production deployment and release approval separate from Codespaces development.

## Current scope and limitations

This setup supports Python runtime development and tests. It does not prove that a Codespace has been created, that the configuration builds on GitHub's hosted environment, or that the project is production-ready. The owner must create the Codespace and capture its actual run evidence.

## Next gates

1. Review and merge this configuration only after CI passes and the owner approves.
2. Create one 2-core Codespace and verify Python 3.12.
3. Run the unit tests, compile check, and deployment preflight; attach evidence.
4. Review Codespaces billing ownership and actual quota usage.
5. Only then prepare an AWS account setup checklist and cost estimate. No AWS infrastructure deployment is authorized by this document.
