# The Echo Panel: When AI Advisors Agree, How Many Independent Opinions Do You Get?

Paras Adlakha (Independent researcher) · Harshita Adlakha (Bangalore Institute of Technology)
AI x Epistemics Research Sprint, Apart Research, 13–15 November 2026 · Tracks 1 and 2

Numbers marked [p] are from the 40-question pilot and will be replaced by the full run.

## Abstract (draft, ~240 words)

Products increasingly answer hard questions with a "panel" of AI advisors: several personas, several samples, or several models, shown side by side. When they agree, people read the agreement as corroboration, much as they would five independent experts. Whether that reading is justified depends on one thing the interface never shows: are the advisors independent once you know the truth? We measure this on 190 binary forecasting questions from ForecastBench that were frozen in July–August 2026 and resolved after every model's training cutoff, each with the prediction market's price as a human-crowd benchmark. We compare five panel designs: one model sampled five times, one model playing five named experts, five models from four developers, the same five after one round of discussion, and the same five after reading a shared research brief. Five personas of one model carry the information of about 1.1 independent advisors [p]; five models from four developers about 1.4 [p]. Pooling the advisors as if they were independent witnesses, the way agreement invites us to, worsens the Brier score by up to 0.11 [p], and unanimous panels were right only 56–73% of the time [p]. AI decision-makers given the same panels did not make this mistake: they averaged, and an independence label changed nothing for them. The over-counting risk sits with people. We specify an independence label that can be computed from a panel's track record, show how a false label could be used to inflate trust, and give a preregistered protocol for testing the label with human readers.

## 1 Introduction (≈1 page)
- Hook: the "ask five AIs" pattern (multi-model chat, persona panels, agent swarms, LLM forecasting ensembles). Agreement feels like evidence.
- Social epistemology: agreement only counts as corroboration when sources are independent given the truth (Goldman 2001; Lackey on dependent testimony). Wisdom-of-crowds results need independent errors and break under social influence (Lorenz et al. PNAS 2011; Becker et al. PNAS 2017). Aggregation with dependent experts (Clemen & Winkler 1985; Winkler 1981).
- People treat AI consensus as social proof (Lee & Lee 2026, N = 127).
- Question and contributions (3 bullets): measurement across product-style panel designs; the cost of the "independent witnesses" reading; the label, its dual use, and a human-study protocol.

## 2 Related work (≈0.75 page)
- LLM monoculture and correlated errors: Kim et al. ICML 2025; Goel et al. ICML 2025; Begin et al. 2026 (N_eff ≈ 1.4 in LLM prediction markets); Aitchison et al. 2026; Denisov-Blanch et al. 2026; Kleinberg & Raghavan PNAS 2021; Bommasani et al. NeurIPS 2022.
- LLM forecasting and silicon crowds: Schoenegger et al. Sci. Adv. 2024; Halawi et al. NeurIPS 2024; Karger et al. ICLR 2025 (ForecastBench); Douven 2026.
- Multi-agent conformity and discussion: Lorenz/Becker; 2026 conformity papers; CAGE-CAL 2026.
- Trust signals and provenance: Cotton-Barratt & Finnveden 2026 (auditability), C2PA, Community Notes (Chuai et al. CSCW 2024).
- What is new here: (a) product-style panel designs, including personas, discussion and a shared brief, measured with the right conditional-independence statistic; (b) the size of the over-counting cost, set against a human crowd; (c) a consumer-side test (AI vs. human reader) and a label specification; (d) prior work by the authors (Planted Post, Sting) and which code is pre-existing.

## 3 Method (≈1.5 pages)
- Data: ForecastBench question sets 2026-07-19 and 2026-08-30; binary market questions resolved 0/1; 190 questions; 38% YES; market price at freeze = human crowd.
- Advisors and panels: five panel types; prompts; temperature 1; market price never shown; every call cached and replayable.
- Measures: conditional correlation ρ|y (why not raw error correlation, illustrated with a synthetic test); n_eff = n / (1 + (n−1)ρ); naive "independent witnesses" pool vs. mean vs. n_eff pool; unanimity accuracy; bootstrap 95% CIs over questions; crowd complementarity.
- AI decision-maker test: four arms (none, generic warning, true label from held-out folds, inflated label n = 5); two decision-maker models.

## 4 Results (≈2.5 pages)
- Fig 1: design. Fig 2: n_eff by panel type with CIs. Fig 3: corroboration premium (Brier of mean vs. naive pool vs. crowd). Fig 4: discussion and shared brief collapse independence (first-round vs. post-discussion n_eff). Fig 5: decision-maker arms ("machines average").
- Table 1: all panels, k, ρ|y, raw ρ, n_eff [CI], Brier (individual, mean, naive, crowd), unanimity accuracy.

## 5 Discussion (≈1 page)
- "Machines average, people count": where the harm actually happens.
- Design implications: show n_eff rather than the number of advisors; do not present personas as experts; diversify developers and evidence, not prompts; protect independence before discussion (Lorenz).
- The independence label as trust infrastructure: computable, auditable, consumable by both people and agents.

## 6 Limitations (≈0.5 page), then References, then appendices
- A. Limitations and Dual-Use / Ethical Considerations (required): no human participants; label untested on people; inflated labels as a manipulation vector; ForecastBench licence; no personal data.
- B. Preregistered human-study protocol for the label.
- C. Prompts, models, cost, and reproducibility.
