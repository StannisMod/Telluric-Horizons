# Sources and evidence

Accessed 2026-11-11. Sources inform implementation but do not replace original game data.

- Official release news: https://store.steampowered.com/news/posts/?appids=281990 — 4.5.4, 1b4f, observed November 11 (latest hotfix announcement). Target release only, not proof of mod compatibility.
- CWTools terraform rule: https://github.com/cwtools/cwtools-stellaris-config/blob/99147efe8072b331005b50536762dcc0b8573224/config/common/terraform_links.cwt — blob b0d6ed2ecba21528c4ffffd7eed593bd5aecca51. Documents resources, duration, country root/from planet scopes, condition, potential, effect and ai_weight.
- CWTools project: https://github.com/cwtools/cwtools-stellaris-config . Full CWTools validation was NOT run; compatibility of this revision with 4.5.3 is not established. Do not count the internal checks as CWTools validation.
- Official wiki https://stellaris.paradoxwikis.com/Planet_modding was inaccessible (401); no claims rely on its current contents.

Original Linux game definitions became available later on November 11 through the user’s licensed installation at /tmp/telluric-stellaris. Launcher metadata and real engine logs identify 4.5.4 (1b4f target checksum from launcher metadata). Read-only inventory and actual engine mounting checks are described in GAME_DATA_AUDIT.md and TEST_REPORT.md. We do not copy or distribute original game files, generated engine documentation, saves or assets. Gameplay/property transfer/DLC/AI remain unverified. No headless execution is claimed.

- Actual SteamCMD anonymous probe: [report and commands](STEAMCMD_REPORT.md), [captured output](evidence/steamcmd-anonymous-281990.txt). App update returned success with zero depots; direct base-depot download returned No subscription. Public app metadata is not access to game definitions.
