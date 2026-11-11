# Generated transition matrix

Model 0.4.0-dev; target 4.5.4 (1b4f).

Base costs only, before country/DLC modifiers. Existing vanilla links are preserved.
New branches yield to usable vanilla candidate links; missing Detox/Hydrocentric unlocks retain the expensive fallback.
All new projects use the common protection/size/deposit filter; Gaia additionally requires World Shaper. Candidate variants have disjoint potential.

| From | To | Energy | Years | Technology | Perk | Variant |
|---|---|---:|---:|---|---|---|
| pc_barren | pc_desert | 14000 | 20 | tech_climate_restoration | — | standard |
| pc_barren | pc_arid | 16000 | 25 | tech_climate_restoration | — | standard |
| pc_barren | pc_savannah | 16000 | 25 | tech_climate_restoration | — | standard |
| pc_barren | pc_continental | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren | pc_ocean | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren | pc_tropical | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren | pc_arctic | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren | pc_tundra | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren | pc_alpine | 19000 | 30 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_desert | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_arid | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_savannah | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_continental | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_ocean | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_tropical | 21000 | 34 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_arctic | 16000 | 24 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_tundra | 18000 | 29 | tech_climate_restoration | — | standard |
| pc_barren_cold | pc_alpine | 18000 | 29 | tech_climate_restoration | — | standard |
| pc_frozen | pc_desert | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_arid | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_savannah | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_continental | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_ocean | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_tropical | 15000 | 25 | tech_climate_restoration | — | standard |
| pc_frozen | pc_arctic | 10000 | 15 | tech_climate_restoration | — | standard |
| pc_frozen | pc_tundra | 12000 | 20 | tech_climate_restoration | — | standard |
| pc_frozen | pc_alpine | 12000 | 20 | tech_climate_restoration | — | standard |
| pc_toxic | pc_desert | 30000 | 40 | tech_climate_restoration | — | standard |
| pc_toxic | pc_arid | 32000 | 45 | tech_climate_restoration | — | standard |
| pc_toxic | pc_savannah | 32000 | 45 | tech_climate_restoration | — | standard |
| pc_toxic | pc_continental | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_toxic | pc_ocean | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_toxic | pc_tropical | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_toxic | pc_arctic | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_toxic | pc_tundra | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_toxic | pc_alpine | 35000 | 50 | tech_climate_restoration | — | standard |
| pc_barren | pc_gaia | 21500 | 30 | tech_climate_restoration | ap_world_shaper | standard |
| pc_barren_cold | pc_gaia | 23500 | 34 | tech_climate_restoration | ap_world_shaper | standard |
| pc_frozen | pc_gaia | 17500 | 25 | tech_climate_restoration | ap_world_shaper | standard |
| pc_toxic | pc_gaia | 37500 | 50 | tech_climate_restoration | ap_world_shaper | standard |
| pc_frozen | pc_gaia | 12500 | 20 | tech_climate_restoration | ap_world_shaper | ready_candidate |
| pc_toxic | pc_gaia | 17500 | 30 | tech_climate_restoration | ap_world_shaper | ready_candidate |

## Preserved and forbidden classes

| Class | Policy | Reason |
|---|---|---|
| pc_desert | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_arid | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_savannah | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_continental | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_ocean | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_tropical | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_arctic | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_tundra | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_alpine | vanilla | Preserve audited vanilla climate links and inhabited-world requirements |
| pc_barren | engineer | Engineered atmosphere and biosphere; class-based abstraction |
| pc_barren_cold | engineer | Engineered atmosphere and biosphere; class-based abstraction |
| pc_frozen | engineer | Engineered atmosphere and biosphere; class-based abstraction |
| pc_toxic | engineer | Engineered atmosphere and biosphere; class-based abstraction |
| pc_molten | forbidden | No supported physically justified ordinary terraforming route |
| pc_gas_giant | forbidden | No supported physically justified ordinary terraforming route |
| pc_asteroid | forbidden | No supported physically justified ordinary terraforming route |
| pc_ice_asteroid | forbidden | No supported physically justified ordinary terraforming route |
| pc_rare_crystal_asteroid | forbidden | No supported physically justified ordinary terraforming route |
| pc_shattered | forbidden | No supported physically justified ordinary terraforming route |
| pc_broken | forbidden | No supported physically justified ordinary terraforming route |
| pc_nuked | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_gaia | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_relic | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_city | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_hive | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_machine | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_ringworld_habitable | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_habitat | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_shrouded | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_volcanic | vanilla | Preserve special, story and DLC mechanics; class presence audited against 4.5.4 |
| pc_machine_broken | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_shielded | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ai | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_infested | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_cybrex | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_nanotech | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_b_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_a_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_f_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_g_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_k_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_m_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_m_giant_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_t_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_black_hole | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_neutron_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_pulsar | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_habitable_damaged | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_tech | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_tech_damaged | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_seam | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_seam_damaged | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_shattered_ring_habitable | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_cosmogenesis_world | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_toxoid_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_rift_star | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_astral_scar | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_gray_goo | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_egg_cracked | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_crystal_habitat | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_warden_guardian | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_crystal_asteroid | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ringworld_shielded | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_habitat_shielded | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_shattered_2 | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_cutholoid | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_junk | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_ark | vanilla | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
| pc_protostar | forbidden | Special, artificial, stellar or story body: preserve original rules; no general engineering links |
