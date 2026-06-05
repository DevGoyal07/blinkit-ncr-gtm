# Where should Blinkit open its next dark store in Delhi NCR?
### A market-entry (GTM) decision, backed by SQL

> **About this project.** A PM case study with a runnable analytical backbone.
> The company context and every economic figure are **real and public** (Eternal/
> Blinkit FY26 reporting — see *Sources*). The pincode-level demand data is
> **illustrative** — Blinkit's order logs are proprietary — so it is *modelled on
> Blinkit's real footprint* (Delhi NCR as the largest market, ~1,300 orders/
> store/day, net AOV ~₹525) and used only for **relative** zone comparison.
> Everything reproduces from the scripts in this repo.

---

## TL;DR — the call

**Launch the next NCR dark store on the Dwarka Expressway / New Gurugram
corridor.** It is the strongest pocket of *unmet, high-value* demand on Blinkit's
NCR growth frontier: ~92k households, demand **+76% in 6 months**, **77% of
demand currently unserved**, only **1 competitor**, and the **highest basket of
any candidate (~₹580 vs Blinkit's ₹525 average)**. It scores **95.3/100** on the
opportunity model — well clear of the field (next corridor: 71.0).

| Decision | Zone | Why |
|---|---|---|
| ✅ **LAUNCH (next store)** | **Dwarka Expressway / New Gurugram** | Biggest *and* highest-AOV unmet demand, fastest growth, only 1 competitor → best unit economics |
| 🟡 **PHASE (next 2–3 stores)** | **Greater Noida West, Sohna Road/SPR, Greater Faridabad** | Real demand, but lower AOV and/or 3-way competition → enter on margin, not discounts |
| 🟠 **DENSIFY (separate track)** | **Indirapuram** | Already has a store but it's capacity-strained (11-min deliveries, 26% SLA breach) → add a *relief* store, not greenfield |
| ⛔ **DON'T** | **Golf Course Road, GK/CR Park** | High demand but **~99% already served** from <2.5 km away → a store here is pure cannibalisation |
| ⛔ **DON'T (yet)** | **Yamuna Expressway/Jewar, Manesar** | Catchment too small to fill a store and break even |

**Why this is on-strategy for Blinkit:** Blinkit turned adjusted-EBITDA
profitable for the first time in Q3 FY26 and explicitly refuses to chase growth
through discounting, guiding mature markets like NCR toward **5–6% of NOV**
margins. Picking the **highest-AOV, lowest-competition** corridor (Dwarka
Expressway) over the bigger-but-cheaper, 3-way-contested one (Greater Noida West)
is exactly that playbook.

---

## 1. The decision to make

Blinkit is the quick-commerce leader — **~2,027 dark stores at end of Q3 FY26,
rising to 2,243 by Q4 FY26, on the way to 3,000+**, with **Delhi NCR as its
single largest market** (public reporting, Eternal FY26). So the GTM question is
*not* "find a coverage desert." For a 2,000-store leader it is:

> **On the NCR growth frontier, which corridor earns the next store — capturing
> the most *incremental, profitable* demand we're losing today — and where should
> we explicitly *not* build because we'd just cannibalise ourselves?**

A good answer needs three things:
1. **Find** the underserved, high-demand corridors from data (SQL).
2. **Recommend** one, with a rollout plan, unit economics, and KPIs (GTM).
3. **Decide** launch / don't / phase — with the trade-off stated, not hidden.

**Audiences:** leadership wants the *call* and the *why*; an analyst wants the
*query* and the *method*. Both are below.

---

## 2. The data

Three tables, a 6-month window (Dec 2025 – May 2026):

| Table | Grain | Key fields |
|---|---|---|
| `orders` | one demand event | `status` (delivered / **unserviceable** / cancelled_other), `order_value`, `delivery_time_min`, `promised_time_min`, `dist_to_store_km`, `area_name`, `order_month` |
| `areas` | one NCR sub-zone | `est_households`, `avg_income_index`, `competitor_count`, `dist_to_nearest_store_km`, `has_own_store` |
| `dark_stores` | one anchor store | location, `launch_date`, `daily_capacity_orders` |

The decisive field is **`status = 'unserviceable'`** — a customer wanted to order
but no store could serve them in the promised window. That is **unmet demand**:
exactly what an ops dashboard hides and what a launch decision turns on.

> **Honest framing of scale.** The `orders` table is a **~10% representative
> extract** (~300k rows) used for *relative* analysis — demand share, growth,
> under-service. The **absolute** numbers in the economics (Section 6) come from
> Blinkit's **real public figures** and bottom-up sizing, cross-checked against
> the extract (×10). The blended AOV in the synthetic data (₹522) deliberately
> matches Blinkit's reported ~₹525.

**Real-data mapping:** delivered/cancelled → order DB; `unserviceable` →
serviceability + app-analytics logs (a "not deliverable to your pincode" wall);
`est_households`/`income_index` → census + geo data; `competitor_count` → field
mapping / Places APIs; `dist_to_nearest_store` → store master + geocoding.

---

## 3. Method — what "underserved high-demand" means

A corridor earns a store when **demand is large and growing**, **we're failing to
serve it today**, and **a new store would be feasible and mostly incremental**
(not stealing from an existing store). I score each candidate (areas **without**
an own store) on four normalised drivers, then layer cannibalisation and
feasibility on top.

| Driver | Proxy | Weight |
|---|---|---|
| Demand size | recent-quarter demand attempts | 0.30 |
| Demand density | attempts per 1,000 households | 0.20 |
| Growth | last-month vs first-month attempts | 0.25 |
| Under-service | % of attempts that are *unserviceable* | 0.25 |

Decision rules:
- **Cannibalisation guard** — already ~fully served by a nearby store (high
  capture %) → a new store mostly cannibalises → **don't**.
- **Feasibility guard** — catchment too small (households) to fill a store → **don't (yet)**.
- **LAUNCH** — top opportunity, underserved, feasible, low cannibalisation.
- **PHASE** — real opportunity that isn't best *right now* (lower AOV/margin,
  competition, or scale/timing) → queue it.
- **DENSIFY** — a *served* zone whose service is degrading from capacity → add a
  relief store (a leader-specific move; query `q6`).

All of this is in **`analysis.sql`** (6 queries). The tables below are the real
outputs of running it.

---

## 4. SQL findings

### 4.1 Demand is rising and the unmet share is widening *(q1)*
NCR-wide demand grows every month — and the share Blinkit **can't** serve climbs
**33.5% → 37.6%**. The frontier gap is getting *worse*, not better.

| Month | Demand attempts | Delivered | Unserviceable % |
|---|---|---|---|
| 2025-12 | 40,327 | 26,816 | 33.5% |
| 2026-02 | 45,203 | 29,170 | 35.5% |
| 2026-05 | 54,715 | 34,167 | **37.6%** |

### 4.2 The corridor scorecard *(q2, recent quarter)*
Mature sectors (Cyber City, Saket, Noida 62) show **<1% unserviceable, ~7-min**
delivery — well covered. The gaps are on the frontier. Note the AOV column — it's
what separates the candidates.

| Zone | Own store? | HH | Dist (km) | Attempts | Unserv. % | Avg delivery | **AOV** |
|---|---|---|---|---|---|---|---|
| **Dwarka Expressway** | No | 92k | 8.4 | 15,660 | **77.0%** | 24.3 | **₹580** |
| Indirapuram | Yes | 80k | 0.0 | 11,850 | 16.5% | **11.0** | ₹473 |
| Sohna Road / SPR | No | 75k | 4.3 | 11,573 | 41.1% | 18.7 | ₹540 |
| Golf Course Road | No | 60k | 2.1 | 9,852 | **0.8%** | 9.6 | ₹601 |
| Greater Noida West | No | 95k | 6.5 | 9,851 | **77.0%** | 22.4 | **₹452** |
| Greater Faridabad | No | 82k | 17.5 | 7,525 | 76.4% | 33.5 | ₹430 |

### 4.3 Where demand is accelerating *(q3)*
| Zone | Dec 2025 | May 2026 | 6-mo growth |
|---|---|---|---|
| Dwarka Expressway | 3,335 | 5,854 | **+75.5%** |
| Sohna Road / SPR | 2,572 | 4,308 | +67.5% |
| Greater Noida West | 2,187 | 3,592 | +64.2% |
| Greater Faridabad | 1,772 | 2,737 | +54.5% |
| *(mature sectors)* | — | — | +11% to +28% |

All the growth is on the frontier; the mature core is flat. Blinkit's *next*
order is being created where it doesn't yet have a store.

### 4.4 Opportunity ranking *(q4)*
| Rank | Zone | HH | Unmet % | AOV | Growth % | **Opportunity /100** |
|---|---|---|---|---|---|---|
| 1 | **Dwarka Expressway** | 92k | 77.0 | **₹580** | 75.5 | **95.3** |
| 2 | Sohna Road / SPR | 75k | 41.1 | ₹540 | 67.5 | 71.0 |
| 3 | Greater Noida West | 95k | 77.0 | ₹452 | 64.2 | 66.9 |
| 4 | Noida Sector 150 | 52k | 77.4 | ₹538 | 53.2 | 57.8 |
| 5 | Greater Faridabad | 82k | 76.4 | ₹430 | 54.5 | 55.9 |

**Dwarka Expressway tops the model by a wide margin (95.3 vs 71.0).** It's the only candidate that is the *biggest*,
*fast-growing*, *almost entirely unserved*, **and** *highest-value*.

### 4.5 The decision table *(q5)*
| Decision | Zones | Logic |
|---|---|---|
| **1 LAUNCH** | **Dwarka Expressway** (opp 95.3) | large + underserved + low cannibalisation + premium AOV |
| **2 PHASE** | Sohna Rd/SPR, Greater Noida West, Noida 150, Greater Faridabad, … | real opportunity; revisit on margin/competition/scale |
| **3 DON'T (cannibalise)** | Golf Course Rd (99.2% captured), GK/CR Park (91.8%) | already served → a store ≈ pure cannibalisation |
| **4 DON'T (sub-scale)** | Yamuna Expressway/Jewar (32k HH), Manesar (35k HH) | catchment too small to fill a store |

### 4.6 Densification check *(q6 — the leader's other lever)*
A 2,000-store leader's "next store" can be a **second store** relieving a strained
catchment. Among *served* zones, one is degrading:

| Zone | Store | Avg delivery | SLA breach % | Flag |
|---|---|---|---|---|
| **Indirapuram** | DS04 | **11.0 min** | **25.8%** | **DENSIFY — add relief store** |
| Cyber City / Saket / Noida 62 / Dwarka / Vasant Kunj | — | 7.1 min | <1% | healthy |

Indirapuram has its own store but demand has outgrown it (16.5% still
unserviceable, deliveries at 11 min vs 7 elsewhere). It belongs on a **separate
densification track**, parallel to the greenfield launch.

---

## 5. GTM recommendation — Dwarka Expressway / New Gurugram

### 5.1 The catchment
A ~5,000–7,000 sq ft store on the Sectors 102–113 belt brings the corridor inside
a ~2.5 km / single-digit-minute radius, converting today's **24-min / 77%-unserved**
experience. Blinkit has publicly flagged that **NCR store rollout is supply-
constrained** (construction/pollution limits) — so this is a corridor where *being
first to stand up capacity* is itself the moat.

### 5.2 Market sizing (bottom-up, cross-checked with the extract)
| Step | Value |
|---|---|
| Households | 92,000 |
| q-commerce-active (~22%, premium corridor) | ~20,000 |
| Orders / active HH / month (~7) | **~140,000 / mo market** (~4,650/day, all players) |
| Measured Blinkit intent today (extract ×10) | ~1,740/day, of which **~1,340/day unmet** |
| Conservative Blinkit share at maturity | **~1,300 orders/day** (≈ Blinkit's network avg per store) |

We plan to ~1,300/day — about the volume *already going unserved* — i.e. a
conservative target with upside.

### 5.3 Rollout plan (phased)
| Phase | Timing | What | Exit gate |
|---|---|---|---|
| **0 — Stand up** | Wk −8→0 | Lease 5–7k sqft; fit-out + cold chain; hire & train ~12–15; localise the **1P assortment** to a premium basket; integrate serviceability | Ops dry-run passes |
| **1 — Soft launch** | Wk 1–2 | Open a tight ≤2.5 km radius; **re-target the corridor's previously-unserviceable customers** (warm, free demand) | p50 ≤ 12 min, fill-rate ≥ 98% |
| **2 — Ramp** | Wk 3–8 | Widen radius; geo-targeted CAC (no deep discounts — on brand); referrals | **≥ 850 orders/day** (past break-even) |
| **3 — Optimise** | Mo 3–6 | Assortment + peak staffing; push utilisation to 80%; **decide Greater Noida West / Sohna Rd next** | **≥ 1,150/day, EBITDA+** |

### 5.4 Unit economics & break-even
*Anchored to Blinkit's real, reported economics (FY26):*

| Lever | Value | Basis |
|---|---|---|
| AOV (this corridor) | **₹560** | above Blinkit's reported ~₹525 (premium catchment) |
| Contribution / order | **₹45** (~8% of NOV) | Blinkit blended is ~₹30 today; mature NCR guided to **5–6% of NOV** — a premium store runs ahead of average |
| Fixed store opex | **₹11 L / month** | ~6k sqft NCR store: rent + staff + cold chain |
| Capex to open | **~₹1.5 Cr** | fit-out/cold chain/devices ~₹65 L + **1P inventory float ~₹85 L** (consistent with Blinkit's ~₹1.5–2 Cr/store under owned-inventory) |
| **Break-even** | **₹11 L ÷ (₹45 × 30) ≈ 815 orders/day** | |

**Ramp vs break-even (~815/day):**

| Month | Orders/day | Monthly EBITDA | Cumulative EBITDA |
|---|---|---|---|
| M1 | 450 | −₹4.9 L | −₹4.9 L |
| M3 | 850 | +₹0.5 L | −₹6.0 L ← *crosses break-even* |
| M6 | 1,250 | +₹5.9 L | +₹6.9 L |
| M12 | 1,300 | +₹6.6 L | +₹46 L |

→ **Store-level EBITDA-positive from ~Month 3; fit-out capex (~₹65 L) paid back
~Month 12–15.** Full-cash payback (incl. the recoverable inventory float) is
longer — which is the honest reality of q-commerce, and why the bet rides on
Blinkit's stated path to **5–6% of NOV** in mature markets like NCR.

### 5.5 Success KPIs
**North-star:** orders/day (gates 450 → 850 → 1,150 → 1,300 at M1/M2-end/M6/M12).

| Type | Metric | Target |
|---|---|---|
| Demand | Orders/day; new-customer adds in the corridor | ramp above |
| Service | Delivery time p50 / p90 | ≤ 12 / ≤ 18 min (vs 24 today) |
| Service | Unserviceable % in corridor | 77% → **<10% in 60 days** |
| Efficiency | Utilisation (orders ÷ ~1,500 cap) | 60% by M3, 80% by M6 |
| Economics | Contribution / order; EBITDA breakeven | ≥ ₹40; by **M3** |
| Economics | **Inventory spoilage** (matters under 1P) | **< 2%** |
| **Guardrail** | Cannibalisation of Cyber City / Dwarka stores | < 10% of new-store volume |
| **Guardrail** | NCR-cluster contribution (not just this store) | net positive |

---

## 6. The decision — launch / don't / phase, with the trade-off

The real tension is **scale vs margin vs cannibalisation**:

| Zone | Call | The trade-off we're accepting |
|---|---|---|
| **Dwarka Expressway** | ✅ **LAUNCH** | ₹1.5 Cr cash + ramp risk + competitor response. Mitigated by the largest *warm* unmet pool, the highest AOV, and only one competitor — the best economics on the board. |
| **Greater Noida West** | 🟡 **PHASE** | The instructive one: it has **more households (95k) and the same 77% unmet**, so raw demand is huge. But **AOV is ₹452 vs ₹580** and **three competitors** are already fighting on price. Entering now means a margin war — the opposite of Blinkit's stated "no growth on discounting" strategy. Greenlight site scouting; enter selectively once we can hold a price-disciplined position, or as store #2 after Dwarka Expressway proves the corridor. |
| **Sohna Rd, Faridabad, Noida 150** | 🟡 **PHASE** | Genuine frontier demand; queue behind the marquee corridor to avoid over-stretching NCR hiring/capital in one cycle. |
| **Indirapuram** | 🟠 **DENSIFY** | Not a new-market decision at all — it's a *relief* store for an over-capacity catchment (q6). Different capex case, different KPIs; runs on a parallel track. |
| **Golf Course Rd / GK–CR Park** | ⛔ **DON'T** | Tempting on raw volume *and* premium AOV, but **~99% already served** from <2.5 km. A store here mostly cannibalises Cyber City/Saket → negative incremental contribution. |
| **Yamuna Expressway / Manesar** | ⛔ **DON'T (yet)** | Sub-scale catchments — can't fill a store at viable utilisation. Revisit as Jewar airport / Manesar density matures. |

**The headline judgment — Dwarka Expressway over Greater Noida West — is the
senior-PM move.** A naive "biggest unmet demand" read points at Greater Noida
West (more households). The model *and* Blinkit's actual strategy point at Dwarka
Expressway: **higher basket, one competitor, better margin, defensible.** The
model finds candidates; the strategy sequences them.

---

## 7. Assumptions & limitations
- **Demand data is illustrative**, modelled on Blinkit's public footprint; the
  *method, SQL, and decision logic* are production-ready. All **economic figures
  are real** Eternal/Blinkit FY26 numbers (see Sources).
- **Unserviceable ≈ intent, and is conservative** — fully suppressed demand
  (users who never open the app in an uncovered corridor) isn't captured, so the
  true opportunity is likely larger.
- **Serviceability is distance-modelled**; production would use live rider ETA,
  traffic, and real store capacity.
- **Cannibalisation is estimated from current capture %** — the real test is a
  **geo holdout / switchback experiment**.

## 8. How I'd validate before signing the lease
1. **Pre-lease pin-drop demand campaign** on the corridor (geo ads → waitlist) to
   confirm the ~1,340/day unmet signal converts.
2. **Geo holdout** around the Cyber City / Dwarka stores to measure true
   cannibalisation.
3. **Real-estate + last-mile walk:** 5–7k sqft availability (NCR construction is
   the real constraint), rider supply, peak-hour ETAs.
4. **Warm-cohort launch list** from previously-unserviceable customers.

---

## Sources (public)
- Eternal Ltd **Q3 FY26** results & shareholder letter (Jan 2026): Blinkit 2,027 dark stores; first adjusted-EBITDA profit (₹4 Cr); NOV ₹13,300 Cr; 243M orders (+121% YoY); ~45–46% QC share; NCR = largest market & supply-constrained; 1P inventory model (~90% of NOV). — *as reported by Inc42, Storyboard18, ET/Business Standard.*
- Eternal Ltd **Q4 FY26** results (Apr 2026): Blinkit 2,243 dark stores; NOV ₹14,386 Cr; adjusted EBITDA ₹37 Cr (~0.3% of NOV); **net AOV ~₹525**; 27.2M monthly transacting customers; mature-market margin guidance **5–6% of NOV**. — *as reported by Entrackr.*
- Blinkit blended **contribution ~₹30/order**; EBITDA loss/order ₹7 (Q2 FY26) vs Instamart ₹84; FY26 capex into Blinkit ~₹1,700 Cr. — *founderpin, JM Financial via Business Standard.*
- Tagline change (Jan 2026) from "10 minutes" to "30,000+ products"; competitor stores (Instamart ~1,136, AOV ₹746; Zepto ~1,100–1,200). — *Storyboard18, Laffaz.*

*Setting: Delhi NCR; company: Blinkit (Eternal Ltd). Real economics, illustrative
demand data. City, thresholds, and scoring weights are all parameters you can
change.*
