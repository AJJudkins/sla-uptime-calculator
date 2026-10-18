# Security policy

## Scope and safety
offline and read-only: it reads one CSV and prints numbers; nothing is written or sent anywhere.

## What was and was not tested
**Tested (automated, in CI and locally):** uptime and budget math, overlapping-incident merging, input validation and exit codes on sample CSVs.

**Not tested:** real monitoring exports, time zones (timestamps are treated as naive local times), and maintenance-window exclusions (not supported).

## Reporting a problem
This is a small personal portfolio project, not a supported product. If you find a security issue, please open a GitHub issue **without** secrets, credentials or real system details, or use GitHub's "Report a vulnerability" button on the Security tab if it is enabled.
