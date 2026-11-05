"""SimplePart stores whose list names are loose (mitsubishipartsgiant, volvopartsgiant):
a row is kept only when BOTH the printed list name (rules) and the product URL's name
slug (/genuine/<make>~<name-slug>~<pn>, slug_rules) name the assembly. The template's
slug_checks option applies the exclusions and the reman test to the slug as well.

product() also marks units the product page itself calls remanufactured (`reman: true`)
or an exchange unit (`exchange_unit: true`, Volvo "Alternator, Exchange"); it never
unmarks what the list page said.
"""
from __future__ import annotations

import re

from . import _simplepart as _sp
from ._simplepart import SimplePart

EXCHANGE = re.compile(r"\bexchange\b", re.I)


class SlugCheckedSimplePart(SimplePart):
    def __init__(self, *args, slug_rules: dict[str, str], **kw):
        super().__init__(*args, slug_checks=True, **kw)
        self.slug_rules = {k: re.compile(v, re.I) for k, v in slug_rules.items()}
        missing = set(self.rules) ^ set(self.slug_rules)
        if missing:
            raise ValueError(f"rules and slug_rules differ: {sorted(missing)}")

    def match(self, cat: str, main: str, aux: str, slug: str = "") -> bool:
        return bool(self.slug_rules[cat].search(slug)) and super().match(cat, main, aux, slug)

    def product(self, product_url: str) -> dict:
        out = super().product(product_url)
        names = " ".join(filter(None, [out.get("description"), out.get("other_names")]))
        if _sp.REMAN.search(names):
            out["reman"] = True
        if EXCHANGE.search(names):
            out["exchange_unit"] = True
        return out
