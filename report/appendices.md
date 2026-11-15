## Appendix A. Limitations and Dual-Use / Ethical Considerations

**What this establishes.** For one question type (binary forecasting questions with no web access, frozen in mid-2026) and the models we could reach this weekend, AI advisor panels built the way products build them carry far fewer independent opinions than their size suggests, and reading their agreement as independent corroboration makes forecasts worse. It also establishes that the two AI decision-makers we tested do not over-count agreement in this setting.

**What it does not establish.**
- *Effect on people.* We ran no human participants. The claim that people over-count AI agreement rests on Lee and Lee (2026) and on the wider social-proof literature, not on our data. Whether our label corrects human readers is untested; Appendix B is the protocol for testing it.
- *Generality.* The models answered without retrieval, so their forecasts are weak (close to the 0.25 Brier of always saying 50%). Panels with search access may be more accurate and more or less independent; a shared search engine could make them less independent. Our questions come from prediction markets, which over-represent politics, crypto and sport.
- *The independent-witnesses pool is a stylised reader.* Real people do not add log-odds. The pool is the formal version of "they all agree, so it must be true", and the premium should be read as an upper bound on the harm of full over-counting, not as an estimate of what any particular person does.
- *Model coverage.* Five models from four developers, all small or mid-sized. Two NVIDIA-hosted models (DeepSeek V4.1 Flash and Kimi K2.6) were unavailable or timed out this weekend and were dropped before the main run; Mistral Large 4 worked but was too slow for the deadline.
- *ρ|y needs both outcome classes.* With 73 YES and 117 NO questions both classes are large enough, but the statistic is noisy for small panels of questions, which is why we report bootstrap intervals.

**Dual use.** The inflated-label arm shows the risk directly: a label is a claim, and a false "5.0 independent advisors" label is an easy way to make a panel look more trustworthy than it is. Anyone who controls the interface could use independence labels to launder confidence. For that reason the label we propose (Section 5) must be computed from a public track record by a party other than the panel's vendor, and must state its sample and date. A second risk is that the method could be used to tune persona prompts so that a panel *appears* more diverse on the statistic without being more informative. Our measure is computed on outcomes, so this would require gaming the forecasts themselves, but a vendor could still choose a flattering question set. Publishing the question set with the label limits this.

**Data and privacy.** We used only public data: ForecastBench question and resolution files (released for research use by the Forecasting Research Institute) and model outputs. No personal data were collected. The market prices are public aggregates. All prompts, outputs and the call cache are released.

**Use of AI tools.** We used AI assistants for coding help, literature search and editing. The authors designed the study, checked every reference against a primary listing, and take responsibility for all claims.

## Appendix B. Preregistered protocol for testing the independence label with people

*Status: designed during the sprint, not yet run. Fixed here so that it can be run unchanged.*

**Question.** When people see a five-advisor AI panel, does an independence label make their confidence track the panel's real informativeness?

**Design.** Online between-subjects experiment, 2 × 3. Factor 1: panel type, shown with real outputs from this study (five personas of one model, n_eff ≈ 1, versus five models from four developers, n_eff ≈ 1.5). Factor 2: note (none; true label; inflated label). Each participant sees 12 resolved questions in random order, with the panel's five probabilities and one-line reasons, and gives (a) their own probability, (b) how much they would rely on the panel (1–7), and (c) whether they would act on it (a binary choice with a stated payoff).

**Primary outcome.** Brier score of participants' probabilities against the real resolutions. Secondary: over-extremity, the participant's |p − 0.5| minus that of the panel average; reliance ratings; and the action error rate.

**Hypotheses.** H1: with no label, participants' probabilities are more extreme than the panel average when the panel is unanimous (over-counting). H2: the true label reduces over-extremity relative to no label. H3: the inflated label increases it (dual-use check). H4: the true label improves Brier scores more for the persona panel than for the mixed panel.

**Sample.** About 600 adults (100 per cell) on Prolific gives 80% power to detect a standardised difference of 0.4 in over-extremity between two cells at α = 0.05 (two-sided), allowing for 10% exclusions. Attention checks are fixed in advance.

**Ethics.** Institutional review before running; informed consent; no deception about the study's purpose beyond the inflated label, which is explained in a debrief that shows each participant the true label for every panel they saw.

**Analysis.** Mixed-effects regression with random intercepts for participants and questions; all exclusions and transformations fixed in this appendix before data collection.
