# Parts-gap curation — 2026-11

The most common cars on the lots matched only the generic commuter rows
(headlights, mirrors, tail lights, the seven consensus evergreens), so their
Pro value lines said little about the car. This pass adds model-specific
rows, one model at a time, with the owner reviewing each before the next.

**Basis for every row**

- *Pull cost*: the median of the category across the 30 yard price lists the
  app already publishes (`docs/data/*_pricing.json`, 2026-11-03), e.g.
  fuel pump $24, throttle body $32, A/C compressor $40, fan assembly $16,
  seat $24 (power seats run higher), alloy wheel $25 each, spoiler $28,
  tail light $23, headlight $10–25.
- *Band*: a conservative used-OEM resale anchor for that exact part, kept
  in line with the audited bands for the same category elsewhere in the
  table (e.g. the Camry/Accord headlight and seat rows). The display pass
  (`_resale_sold_calibrate`) scales anchors down toward sold prices, and
  the live eBay feed (`ebay_prices.py`) replaces each band with real
  listing data once the keys exist. These anchors are placeholders for
  that, not claims of measured sold prices.
- *Gates*: options (spoilers, leather, wheels, HID) are flagged `option`
  so they ship "if equipped" and add $0 to ranking; coupe-only parts use
  the new `body` gate, which the VIN decode confirms or excludes.
- Never engines, transmissions or catalytic converters.

## 1. Nissan Altima (8,700 cars tracked; #3 nationally)

Generations: L31 2002–2006 · L32 2007–2012 (sedan + 2008–2013 coupe) ·
L33 2013–2018 · L34 2019+.

| Row | Years | Gate | Why |
|---|---|---|---|
| Electronic Steering Column Lock (ESCL) | 2007–2012 | — | Push-button start was standard on every L32; the ESCL is the generation's famous failure (dealer fix $800+), so working used units sell steadily. Overlay row widened from 2009-only. |
| Fuel Pump Module | 2002–2018 | — | Common DIY replacement on QR25/VQ35 cars; cheap pull, reliable seller. |
| Electronic Throttle Body | 2002–2018 | — | Known QR25DE failure point; match the part number across the three generations. |
| A/C Compressor | 2002–2018 | — | High-population application; verify the clutch spins. |
| Radiator Fan Assembly | 2002–2018 | — | Dual-fan assembly, frequent failure, low pull cost. |
| Rear Spoiler (factory) | 2002–2018 | option | Trim-package option on every generation. |
| Leather Power Driver Seat (SL) | 2007–2018 | option | SL package; never VIN-decodable. |
| 17"/18" Alloy Wheels (set) | 2007–2018 | option | SE/SL/SR wheels; set price, local sale. |
| HID Xenon Headlights (pair) | 2010–2012 | option | 3.5 SR premium package only; rare. |
| Headlights w/ LED Signature (facelift) | 2016–2018 | — | The 2016 facelift lamps resell well above the pre-2016 halogen row, which now stops at 2015. |
| Coupe Tail Lights (pair) | 2008–2013 | body: coupe | Coupe-only lamps, far fewer cars built. |
| Coupe Headlights (pair) | 2008–2013 | body: coupe | Same. |

Also: the overlay's Bose row extended 2005–2012 (the base entry covers
2013+).

Not added, on purpose: CVT (transmission), QR25DE/VQ35 engines, catalytic
converter, key fobs (programming), ignition coils (cheap new).
