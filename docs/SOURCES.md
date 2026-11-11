# Sources and evidence

Accessed 2026-11-11. Sources inform implementation but do not replace original game data.

- Official release news: https://store.steampowered.com/news/posts/?appids=281990 — 4.5.4, 1b4f, observed November 11 (latest hotfix announcement). Target release only, not proof of mod compatibility.
- CWTools terraform rule: https://github.com/cwtools/cwtools-stellaris-config/blob/99147efe8072b331005b50536762dcc0b8573224/config/common/terraform_links.cwt — blob b0d6ed2ecba21528c4ffffd7eed593bd5aecca51. Documents resources, duration, country root/from planet scopes, condition, potential, effect and ai_weight.
- CWTools project: https://github.com/cwtools/cwtools-stellaris-config . Full CWTools validation was NOT run; compatibility of this revision with 4.5.3 is not established. Do not count the internal checks as CWTools validation.
- Official wiki https://stellaris.paradoxwikis.com/Planet_modding was inaccessible (401); no claims rely on its current contents.

Original Linux game definitions became available later on November 11 through the user’s licensed installation at /tmp/telluric-stellaris. Launcher metadata and real engine logs identify 4.5.4 (1b4f target checksum from launcher metadata). Read-only inventory and actual engine mounting checks are described in GAME_DATA_AUDIT.md and TEST_REPORT.md. We do not copy or distribute original game files, generated engine documentation, saves or assets. Gameplay/property transfer/DLC/AI remain unverified. No headless execution is claimed.

- Actual SteamCMD anonymous probe: [report and commands](STEAMCMD_REPORT.md), [captured output](evidence/steamcmd-anonymous-281990.txt). App update returned success with zero depots; direct base-depot download returned No subscription. Public app metadata is not access to game definitions.

## 0.3.0 follow-up

- Read-only vanilla deposit metadata: common/deposits/99_README_DEPOSITS.txt, ordinary orbital deposit definitions, terraforming swap flags and native on_actions. Source files and engine documentation remain outside this repository. The chosen policy is native processing with explicit special-deposit preflight, not a claim of measured preservation.
- Native Wilderness helpers: common/inline_scripts/terraform/wilderness_biomass.txt and corresponding scripted effects. Only references are emitted. Native AI trigger signatures were checked against locally generated 4.5.4 engine documentation.
- Official CWTools release metadata checked via https://api.github.com/repos/cwtools/cwtools/releases/latest : c0.0.16-alpha2, published 2022-03-04, no downloadable assets in that response. Official rule head checked via https://api.github.com/repos/cwtools/cwtools-stellaris-config/commits/master : 99147efe8072b331005b50536762dcc0b8573224, 2026-06-11. These facts do not prove incompatibility, but provide no confirmation of 4.5.4 support. CWTools was not installed/run and is not counted as validation.
- External installed Size Matters! (Widget), version 1.0, Workshop folder 3674707848: descriptor, four script files, interface and localisation inspected read-only. No original mod content is distributed. Structural comparison is recorded in COMPATIBILITY.md; runtime remains untested.

- 0.4.0 technology ordering verified from local common/technology/00_soc_tech.txt and Russian technology localisation: terrestrial_sculpting tier 2; ecological_adaptation tier 3 and climate_restoration tier 4 both depend directly on terrestrial_sculpting. World Shaper requires climate_restoration in ordinary perk selection. Native Gaia baseline and the special previously_terraformed_planet restoration were read from terraform definitions and their event setters; no source scripts copied.
