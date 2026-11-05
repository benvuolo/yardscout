#!/usr/bin/env python3
"""policy.py: values the spec fixes, tables copied from other files stay in
sync with their sources, and nothing is confirmed without an audit."""
import re

from _util import OEM, check, done
import policy

check("evidence age 120 days (§0 #8)", policy.EVIDENCE_MAX_AGE_DAYS == 120)
check("universal cap 12 feed models (§0 #9)", policy.UNIVERSAL_CAP == 12)
check("systemic failure rate 2% (§0 #11)", policy.SYSTEMIC_FAIL_RATE == 0.02)
check("thin universe needs 5 records from 3 categories (§0 #7)",
      policy.TRIMU_MIN_RECORDS == 5 and policy.TRIMU_MIN_CATS == 3)
check("chain depth 4 (R4)", policy.CHAIN_DEPTH == 4)
check("payload budget 1.3 MB (V11)", policy.PAYLOAD_BYTE_BUDGET == 1_300_000)
check("each site belongs to exactly one namespace",
      len(policy.SITE_NS) == sum(len(d["sites"]) for d in policy.NAMESPACES.values()))
fetch_src = (OEM / "fetch.py").read_text()
check("every namespace site is on fetch.py ALLOWED", all(s in fetch_src for s in policy.SITE_NS))
check("the aftermarket track is never a namespace", not (policy.AFTERMARKET_SITES & set(policy.SITE_NS)))
check("CATEGORY_STATUS: nothing is confirmed without a full audit record",
      all(rec.get("errors") == 0 and rec.get("sample_n") and rec.get("auditor_session") and rec.get("policy_sha256")
          and rec.get("raw_commit") for site in policy.CATEGORY_STATUS.values() for rec in site.values()))
check("CATEGORY_STATUS is empty today (no audit has run)", policy.CATEGORY_STATUS == {})
check("PartsGiant engine cells are not reliable (§4)",
      not any(v for s, v in policy.ENGINE_CELLS_RELIABLE.items() if s not in policy.SIMPLEPART_SITES))
for site, flag in policy.OPTION_COLUMN_IS_TRIMS.items():
    name = site.replace("www.", "").rsplit(".", 1)[0]
    src = (OEM / "sites" / f"{name}.py").read_text()
    check(f"OPTION_COLUMN_IS_TRIMS[{name}] matches the site module",
          bool(re.search(r"option_column_is_trims\s*=\s*True", src)) == flag)
for name in ("fordpartsgiant", "nissanpartsdeal", "infinitipartsdeal", "hyundaipartsdeal", "kiapartsnow"):
    src = (OEM / "sites" / f"{name}.py").read_text()
    site = f"www.{name}.com"
    check(f"{name}: options are not trims (absent from OPTION_COLUMN_IS_TRIMS)",
          not re.search(r"option_column_is_trims\s*=\s*True", src) and site not in policy.OPTION_COLUMN_IS_TRIMS)
audit = (OEM / "AUDIT.md").read_text()
sec = audit.split("## Exclude at curation", 1)[1].split("\n## ", 1)[0]
rows = re.findall(r"^\|\s*(www\.[^|]+?)\s*\|\s*([a-z-]+)\s*\|\s*([A-Z0-9-]+)\s*\|", sec, re.M)
check("EXCLUDE_AT_CURATION equals AUDIT.md's 'Exclude at curation' table",
      {(a, b, c) for a, b, c in rows} == set(policy.EXCLUDE_AT_CURATION), f"{rows} vs {list(policy.EXCLUDE_AT_CURATION)}")
check("reman syntax: Toyota -84 and R+digit (withhold only)",
      policy.is_reman_pn("toyota", "28100-20020-84") and policy.is_reman_pn("mopar", "R5233006")
      and not policy.is_reman_pn("mopar", "4801477AG") and not policy.is_reman_pn("nissan", "23100-JA184"))
check("pn keys never merge across namespaces", policy.pn_key("toyota", "1234-5") != policy.pn_key("mopar", "1234-5"))
check("pn keys strip punctuation only (no suffix interpretation)",
      policy.pn_key("hmg", "37300-2G600") == policy.pn_key("hmg", "373002G600")
      and policy.pn_key("toyota", "87910-06925") != policy.pn_key("toyota", "87910-06925-B0"))
check("rule-4 pattern catches engines, transmissions and converters",
      all(policy.RULE4_RE.search(x) for x in ("Engine Assembly", "Long Block", "Transmission Assy", "Transaxle",
                                              "Catalytic Converter")))
check("VIN position 1 'L' is China, never Korea (ISO 3779)", policy.PLANT_FROM_VIN0["L"] == "CN")
check("every source file named in policy_sha256 exists",
      all((OEM / f).exists() for f in ("policy.py", "notes.py", "positions.py", "model_map.json")))
done("test_policy")
