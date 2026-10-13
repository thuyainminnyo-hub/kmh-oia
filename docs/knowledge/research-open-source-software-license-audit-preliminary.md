# KMH Research Register — OSS License Audit (Preliminary)

**Register ID:** KMH-RESEARCH-OSS-LIC-001  
**Date:** 2026-10-13  
**Status:** Preliminary desk review; NOT legal approval and NOT production adoption approval.  
**Parent research:** [Open-Source Software Alternatives Round 1](https://github.com/thuyainminnyo-hub/kmh-oia/blob/main/docs/knowledge/research-open-source-software-alternatives-round-1.md)

## Preliminary license findings

| Project | Initial license finding | Primary source | Review status |
|---|---|---|---|
| Krita | GPL-3.0; project notes some individual files may have different compatible licenses | https://krita.org/en/about/license/ and https://github.com/KDE/krita | Preliminary source found; check bundled components before redistribution |
| GIMP | GPL-3.0-or-later for core; libraries and other assets may carry separate licenses | https://www.gimp.org/docs/userfaq.html and https://github.com/GNOME/gimp/blob/master/LICENSE | Preliminary source found; inspect components/plugins/assets |
| Inkscape | GPL-2.0 for program, packages, extensions and source as described on official license page | https://inkscape.org/en/about/license/ | Preliminary source found; inspect included extensions and dependencies |
| LibreOffice | MPL-2.0-based licensing with code from other projects and additional open-source licenses; exact installation components can vary | https://www.libreoffice.org/licenses/ | Multi-license review required |
| Penpot | MPL-2.0 source notice in upstream repository | https://github.com/penpot/penpot | Preliminary source found; review any deployment, dependencies and bundled assets |
| FreeCAD | LGPL-2.1-or-later for application source; documentation has a separate license | https://github.com/FreeCAD/FreeCAD and https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/License.md | Preliminary source found; review third-party libraries separately |

## What this does and does not mean

- The findings identify primary license information for the upstream projects; they are not a substitute for reviewing the exact version, binary package, dependencies, plugins, fonts, templates, or assets KMH intends to use.
- Running software internally is different from redistributing it, modifying and distributing a build, embedding its code, or distributing plugins. Obligations can differ by activity and component.
- A software license does not automatically grant rights to third-party content created with or bundled alongside the software.
- Do not conclude that a project is legally cleared for every KMH use solely from its top-level license label.

## KMH decision rule

1. **Internal evaluation:** may proceed only with trusted official distribution and security checks.
2. **Production use:** requires task-fit, compatibility, security and maintenance checks.
3. **Redistribution, modification, embedding or plugin distribution:** requires a specific obligation review for that activity.
4. **Unknown license / provenance:** HOLD.
5. Keep version number, source URL, license text, date checked and evidence snapshot in the project record.

## Immediate next step

Choose the first candidate based on an actual KMH workflow requirement. Before installing or integrating it, check its current stable release, security advisories, supported platform and the precise package/license metadata. This audit has not run any software or approved any candidate for production.
