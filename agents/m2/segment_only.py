"""Segment-only mode: no HCP rows available. specs/m2-segmentation.md:
'Build segments from specialty x setting x city tier ... produce sizes and
tiers without HCP lists; flag mode=segment_only.'

There's no real prescriber-count-by-segment source in this repo yet (M1's
MarketLandscape has no structured prescriber breakdown, and there are no HCP
rows here by definition) — so "sizes" here are directional, relative
categorical-weight products, not real headcounts. Every segment this produces
is flagged mode="segment_only" and carries a note saying so.
"""

from __future__ import annotations

import itertools

from models.scores import percentile_rank
from schemas.brand import Brand
from schemas.enums import Tier
from schemas.hcp import Segment
from schemas.pack import Pack

SEGMENT_ONLY_NOTE = "directional only: segment-only mode has no real HCP-level headcounts"


def run_segment_only(brand: Brand, pack: Pack, target_share: float) -> list[Segment]:
    proxies = pack.potential_proxies
    if not proxies or not (
        proxies.specialty_weight and proxies.setting_weight and proxies.city_tier_weight
    ):
        return []

    combos = [
        (specialty, setting, city_tier)
        for specialty, setting, city_tier in itertools.product(
            proxies.specialty_weight, proxies.setting_weight, proxies.city_tier_weight
        )
    ]
    relative_potentials = {
        combo: (
            proxies.specialty_weight[combo[0]]
            * proxies.setting_weight[combo[1]]
            * proxies.city_tier_weight[combo[2]]
        )
        for combo in combos
    }
    population = list(relative_potentials.values())

    segments = []
    for combo in combos:
        specialty, setting, city_tier = combo
        relative_potential = relative_potentials[combo]
        pctl = percentile_rank(relative_potential, population)
        # No share/rung/reachability exist without HCP rows, so tiering here
        # can only use the potential-percentile axis — t2_defend (which needs
        # a real adopter/advocate rung) is unreachable in this mode.
        if pctl >= 70:
            tier = Tier.t1_grow
        elif pctl >= 30:
            tier = Tier.t3_develop
        else:
            tier = Tier.t4_nurture

        segments.append(
            Segment(
                brand_id=brand.id,
                name=f"{specialty} / {setting} / {city_tier}",
                rule={"specialty": specialty, "setting": setting, "city_tier": city_tier},
                tier=tier,
                hcp_count=0,
                total_potential=relative_potential,
                avg_share=0.0,
                target_share=target_share,
                intent=SEGMENT_ONLY_NOTE,
                mode="segment_only",
            )
        )

    return segments
