title: The Echo Panel: When AI Advisors Agree, How Many Independent Opinions Do You Get?
authors: Paras Adlakha | Independent researcher; Harshita Adlakha | Bangalore Institute of Technology
abstract: AI products increasingly answer hard questions with a panel: several models, several personas of one model, or several agents that confer before replying. When the panel agrees, people read the agreement as corroboration. That reading is justified only if the advisors are independent once the truth is known, and no interface shows whether they are. We measured this on 190 forecasting questions from ForecastBench that resolved after every model's training cutoff, using each question's prediction-market price as a human benchmark. Five personas played by one model carried the information of 1.1 to 1.2 independent advisors, no more than asking the model five times. Five different OpenAI models carried 1.47, and a panel spanning four developers did no better (1.41). One round of discussion cut the five-model panel to 1.10 and raised the share of unanimous answers from 56% to 84%, while unanimous panels were no more often right (70% before, 68% after). Treating the advisors as five independent witnesses made the panels look 92% to 95% sure and worsened their Brier scores by 0.065 to 0.127; they were right 56% to 68% of the time. Two AI decision-makers did not make this mistake: they averaged the panel, and an independence label, true or false, changed nothing. The risk therefore sits with human readers, who are known to treat AI consensus as social proof. We specify an auditable independence label, describe how a false label could inflate trust, and give a preregistered protocol for testing the label with people.

## 1 Introduction

Ask a modern assistant a hard question and you may get more than one answer back. Multi-model chat apps put several models side by side, "panel of experts" prompts have one model speak as an economist and a political scientist, and agent frameworks let several copies of a model confer before reporting. The user sees a group, and a group that agrees looks like a stronger case than one voice.

Whether it is a stronger case depends on something the interface never shows. Goldman (2001), asking how a layperson should weigh agreeing experts, put it plainly: a second expert who agrees adds evidence only to the extent that her opinion did not simply come from the first. Statistically, dependent sources carry far less information than independent ones, with a hard ceiling no matter how many you add (Clemen & Winkler, 1985). The wisdom of crowds rests on this independence, and social influence erodes it quickly (Lorenz et al., 2011; Becker et al., 2017).

AI panels have reason to fail this test. Language models share training data, recipes and often retrieved documents, and models from different developers make strikingly similar mistakes (Kim et al., 2025; Goel et al., 2025). People, meanwhile, treat AI agreement as social proof: in a controlled study, a unanimous set of agents moved users' opinions faster and inflated their confidence (Lee & Lee, 2026).

We ask a question that sits between these findings and the products people use: **when a person consults an AI panel and the panel agrees, how many independent opinions did they actually get, and what does it cost to treat the agreement as corroboration?** In his talk at this sprint, Palermos described AI as one partner in a socio-technical system of knowing. On that view the thing to evaluate is the panel together with the person reading it, and independence matters at the moment of reading.

We make three contributions. (1) On 190 forecasting questions that resolved after every model's training cutoff, we measure the independence of five product-style panel designs (one model sampled five times, five personas of one model, five different models, the same five after one round of discussion, and after a shared research brief) using the statistic that the "agreement as corroboration" reading assumes: correlation between advisors once the outcome is known. (2) We price over-counting by comparing an independent-witnesses reading with an honest average, against the prediction market's own forecast. (3) We test whether AI decision-makers over-count, with no note, a true independence label or a false one, and give a protocol for testing the label with people.

## 2 Related work

**Correlated errors.** When many decision-makers adopt the same algorithm, welfare can fall even if the algorithm is accurate (Kleinberg & Raghavan, 2021), and models built on shared components fail the same people (Bommasani et al., 2022). Across hundreds of language models, larger and more accurate models from different developers agree more on their mistakes (Kim et al., 2025); this similarity biases LLM judges and grows with capability (Goel et al., 2025). Polling many samples does not make answers more truthful when no verifier exists, because the errors are shared (Denisov-Blanch et al., 2026).

**AI forecasting crowds.** An average of twelve models matched a human tournament crowd on 31 questions (Schoenegger et al., 2024), and retrieval-based systems and a contamination-free benchmark followed (Halawi et al., 2024; Karger et al., 2025). In 2026, Aitchison et al. found that frontier models make highly correlated forecasts, so the best ensembles favour diverse models over many models; Begin et al. reported an effective crowd size of about 1.4 for ten preference-tuned agents; and Douven showed how training-cutoff contamination inflates such results.

**Discussion and conformity.** Seeing each other's estimates narrows a group's spread without making it more accurate (Lorenz et al., 2011), and network structure decides whether discussion helps (Becker et al., 2017). LLM agents conform strongly to a majority (Hussain & Nielbo, 2026), and post-communication agreement can overstate reliability (Huang et al., 2026). Stray's talk at this sprint described feedback loops between conflict and knowledge; agent discussion is one place where such a loop can turn disagreement into false consensus.

**What is new here.** Prior work measures model similarity on benchmark accuracy, or diversity among forecasting systems built to be accurate. We measure the panel designs that products ship (personas, discussion, a shared brief) with the conditional-independence statistic that a reader's inference relies on, price the cost of over-counting against a human crowd, and test the consumer side, where AI and human readers turn out to fail differently. Track 2 of this sprint asks for trust signals that people and machines can both use, and Cotton-Barratt and Finnveden (2026) argue that such tools must be auditable from the start; our label is designed with both in mind. The authors' earlier sprint projects (the Planted Post and the Sting) share the habit of holding everything fixed but one element. Only a model-client helper is reused from them, and it is marked as pre-existing in the code.

![Figure 1: The design. Five ways to build a five-advisor panel on the same question; the market price is the human benchmark and is never shown to the models.](docs/img/fig1_design.png){width=6.0}

## 3 Method

### 3.1 Questions

We use ForecastBench (Karger et al., 2025), which publishes questions every two weeks along with their later resolutions. We took the question sets frozen on 19 July and 30 August 2026 and kept binary questions from Polymarket, Metaculus, Manifold and INFER that had resolved to YES or NO by the 25 October resolution file. That leaves 190 questions, 73 of which (38%) resolved YES. They cover elections, conflicts, markets, sport, technology and science. Every question resolved after the training cutoff of every model we query, so no model can know the answer. Each question carries the market's probability on its freeze date. We use that number as the human crowd's forecast and never show it to the models.

### 3.2 Advisors and panels

Every panel has five advisors. Each advisor gets the question, its resolution criteria, its background text, the freeze date as "today's date", and the closing date. It returns a probability and a one-sentence reason as JSON. Temperature is 1. The five panel types (Figure 1) differ only in where the five answers come from:

- **Same model ×5:** one model asked five times with an identical prompt (gpt-4.1-mini and gpt-5.4-mini).
- **Five personas:** one model told it is a political scientist, an economist, a superforecaster, an investigative journalist and a risk analyst. This is the "panel of experts" pattern.
- **Five models:** gpt-4.1-mini, gpt-5.4-mini, gpt-4o-mini, gpt-5-mini and gpt-4.1. These differ in size, generation and reasoning mode but share a developer.
- **After discussion:** the same five models answer, then each sees the other four answers and reasons and gives a final forecast. We keep both rounds, so the first round is the "five models" panel itself.
- **After a shared brief:** gpt-4.1-mini writes a 120-word neutral research brief, with no probability in it, and all five models read it before answering. This mimics a pipeline with one retrieval step and many reasoners.

A cross-developer version (gpt-4.1-mini, gpt-5.4-mini, Gemma 4 31B, Qwen 3.8 27B and Nemotron 3.5 30B) served as a robustness check; its hosted open-weight endpoints rate-limited heavily during the sprint, so it covers the questions it completed (172 plain, 147 after discussion, 175 with the brief).

Every model call is cached on disk under a hash of the model, messages and sample index, so every number in this report can be recomputed from the released cache without new calls.

### 3.3 Measuring independence

A reader who treats agreeing advisors as independent witnesses is assuming they are **conditionally independent given the truth**: once you know how the question resolved, one advisor's forecast tells you nothing about another's. This is the assumption behind Condorcet's jury theorem and naive Bayes. We measure how far it fails with ρ|y, the average pairwise correlation between advisors' log-odds forecasts within each outcome class, weighted by class size.

We do not rely on the raw correlation of errors (p − y), the usual statistic in the forecasting literature. With yes/no outcomes the shared term y dominates the errors, so the raw correlation is high even for advisors who are independent given the truth (in a synthetic test in our code, ρ|y ≈ 0 while raw error correlation exceeds 0.5). We report it only for comparison.

From ρ|y we compute the **effective number of independent advisors**, n_eff = n / (1 + (n − 1)ρ), the design-effect formula of Kish (1965). Five independent advisors give n_eff = 5; five copies of one opinion give n_eff = 1. We report 95% bootstrap intervals (2,000 resamples of questions). All panel types are compared on the same questions.

### 3.4 The cost of over-counting

We compare two ways of combining the five forecasts. The **average** is the mean probability. The **independent-witnesses pool** adds the advisors' log-odds, starting from even odds: logit(p) = Σ logit(p_j). This is the correct posterior if the advisors really are conditionally independent and each has reported its own likelihood ratio, and it is roughly what "all five agree, so it must be very likely" amounts to. We score both with the Brier score (lower is better; always answering 50% scores 0.25) and set them against the market crowd. The **corroboration premium** is the Brier score of the independent-witnesses pool minus that of the average. We also report how often all five advisors leaned the same way, and how often a unanimous panel was right.

### 3.5 An AI decision-maker and the independence label

To see whether an AI reader over-counts agreement, we give a decision-maker model the question and the panel's five probabilities and reasons, and ask for its own final forecast. Four arms differ only in one sentence under the panel: no note; a generic warning ("these advisors may not be independent of each other"); the true label ("on past questions, the errors of these five advisors were correlated (average r = ρ). Together they carry about the information of N independent advisors, not 5", with N and ρ estimated on the other four-fifths of questions so that no question informs its own label); and an inflated label with r = 0.00 and N = 5.0. The inflated arm is a false claim of full independence and also checks that the reader responds to the number at all. gpt-5.4-mini reads gpt-4.1-mini's panels and vice versa, and both read the post-discussion five-model panel.

## 4 Results

Table 1 gives every panel on the same 190 questions. Figure 2 shows effective independence and Figure 3 what discussion and a shared brief do; Appendix C plots the cost of over-counting and the AI decision-makers.

Table 1: Five-advisor panels on 190 resolved questions. ×5: one model sampled five times; 4.1-mini and 5.4-mini are gpt-4.1-mini and gpt-5.4-mini. ρ|y: mean correlation between advisors within each outcome class. Raw ρ: correlation of errors (p − y), shown for comparison only. n_eff: effective independent advisors with 95% bootstrap CI. Brier scores: mean individual advisor, panel average, and the independent-witnesses pool. Unanimous: share of questions where all five leaned the same way, and the share of those the panel got right. Human market crowd Brier: 0.140.
| Panel | ρ given y | Raw ρ | n_eff [95% CI] | Brier one | Brier avg | Brier 5 witnesses | Unan. / right |
|---|---|---|---|---|---|---|---|
| ×5, 4.1-mini | 0.85 | 0.97 | 1.13 [1.09, 1.19] | 0.276 | 0.270 | 0.397 | 80% / 59% |
| ×5, 5.4-mini | 0.88 | 0.97 | 1.10 [1.08, 1.13] | 0.238 | 0.231 | 0.309 | 76% / 72% |
| Personas, 4.1-mini | 0.79 | 0.97 | 1.20 [1.15, 1.26] | 0.266 | 0.259 | 0.369 | 77% / 60% |
| Personas, 5.4-mini | 0.88 | 0.97 | 1.11 [1.08, 1.14] | 0.229 | 0.223 | 0.288 | 78% / 72% |
| 5 models | 0.60 | 0.90 | 1.47 [1.37, 1.60] | 0.254 | 0.232 | 0.317 | 56% / 70% |
| 5 models, discussed | 0.89 | 0.98 | 1.10 [1.06, 1.14] | 0.246 | 0.241 | 0.322 | 84% / 68% |
| 5 models, shared brief | 0.72 | 0.94 | 1.29 [1.22, 1.37] | 0.229 | 0.216 | 0.286 | 65% / 71% |

**Five voices carry little more than one opinion.** Asking one model five times gives 1.10 to 1.13 effective advisors. Giving the five calls different expert personas changes little: 1.11 for gpt-5.4-mini, where the persona panel is statistically indistinguishable from plain resampling (difference +0.003, 95% CI −0.025 to +0.030), and 1.20 for gpt-4.1-mini (difference +0.065, CI +0.021 to +0.120). Five different OpenAI models do better at 1.47, a gain of 0.36 opinions over personas (CI +0.27 to +0.48). That still leaves about two-thirds of the panel's apparent size as echo. The raw error correlation is 0.90 or higher for every panel and cannot tell these designs apart; the conditional statistic can.

Crossing developers did not buy more independence. The cross-developer panel (two OpenAI models with Gemma 4, Qwen 3.8 and Nemotron 3.5) was worth 1.41 advisors (CI 1.31 to 1.53) on the 172 questions it completed, against 1.42 (CI 1.33 to 1.54) for the five OpenAI models on the same questions. The three open-weight models from different developers were more alike than the OpenAI models were (pairwise ρ|y of 0.70 to 0.73, against 0.52 to 0.62 between gpt-4.1-mini and the open-weight models). This matches the finding of Kim et al. (2025) that a different provider does not guarantee different errors.

![Figure 2: Effective number of independent advisors per panel (190 questions; 95% bootstrap CIs). Dashed lines mark one opinion and five independent advisors.](docs/img/fig2_neff.png){width=4.7}

**Over-counting is expensive.** Treating the five advisors as independent witnesses made every panel worse (Table 1; Figure C1). The Brier penalty ranged from 0.065 (CI 0.037 to 0.094) for gpt-5.4-mini personas to 0.127 (CI 0.097 to 0.160) for gpt-4.1-mini resampled. Read this way, the panels looked between 92% and 95% sure on average, while the side they favoured turned out right in only 56% to 68% of questions. Log loss roughly doubled (for example, 0.66 to 1.30 for the five-model panel). Averaging the five advisors helped only a little over a single advisor (Brier gains of 0.006 to 0.022), which is what low independence predicts.

**Talking erases what diversity bought.** After one round in which each model saw the other four answers, independence fell from 1.47 to 1.10 (difference −0.37, CI −0.47 to −0.28), the level of a single model asked five times. The panel looked far more certain: the share of questions on which all five agreed rose from 56% to 84% (+28 points, CI +22 to +35). It did not become more accurate. Unanimous panels were right 70% of the time before discussion and 68% after, and the panel average's Brier score got slightly worse (+0.009, CI +0.001 to +0.018). The cross-developer panel showed the same collapse: on the 139 questions with both rounds, independence fell from 1.38 to 1.06 (CI 1.03 to 1.10) and unanimity rose from 63% to 88%, with unanimous panels right 72% of the time before and 70% after. This is the pattern Lorenz et al. (2011) found in people, now in a panel of models: exchange narrows the spread of opinion and gives a false sense of confidence. A shared brief did something milder. It cost some independence (1.29, a fall of 0.18, CI −0.28 to −0.10) and raised unanimity by 9 points, but it also made the average a little more accurate (Brier −0.015, CI −0.027 to −0.003). The brief added information and shared it with everyone at once.

![Figure 3: Five OpenAI models with no exchange, after reading one shared brief, and after one round of discussion.](docs/img/fig4_discussion.png){width=5.6}

**The human crowd was better.** Without web access every AI panel was near the 0.25 Brier of always answering 50%, while the market scored 0.140. The panels' errors were only weakly correlated with the market's once the outcome is known (ρ|y 0.25 to 0.30), but they were too inaccurate to help: an equal blend of panel and market (Brier 0.156 to 0.174) was worse than the market alone.

**AI readers average.** The two decision-maker models did not over-count. Across six panel-and-reader pairs and 190 questions, their final forecast was usually within a percentage point of the panel's mean (median distance 0.6 points; mean 2.3 points, with gpt-5.4-mini moving further than gpt-4.1-mini), and its Brier score stayed within 0.012 of the plain average's (Figure C2). This held even for unanimous panels: on more than 900 unanimous cases, the readers were no more confident than the panel average (mean extremity shift between −0.007 and +0.002). Because there was no over-counting to correct, the independence label had nothing to do. No arm differed reliably from "no note" (all 95% intervals for label minus none include zero), and the false "5.0 independent advisors" label did not push the readers toward the five-witness reading either.

## 5 Discussion

**Machines average, people count.** We expected the harm to show up in AI readers, and it did not: the models we tested treat a panel as estimates to average. The documented risk sits with people, who read unanimity as social proof (Lee & Lee, 2026). Product panel designs produce plenty of unanimity and little independent evidence; after one round of discussion, a five-model panel agreed on 84% of questions and was worth 1.1 opinions.

**What this means for design.** The number of advisors on screen overstates the evidence by a factor of three to five, so an interface should show something closer to n_eff than to n. Personas add almost no independent information, and calling them "experts" invites the reading that fails here. If independence matters, protect it before the panel talks: collect forecasts separately and show them side by side, as Lorenz et al. advise for human groups. Models from other developers did not help on our data; giving each advisor different evidence is the remaining lever, and one we did not test.

**The independence label as trust infrastructure.** The label is one number with a stated basis ("these advisors' errors were correlated, r = 0.60; together they carry about the information of 1.5 independent advisors, not 5"). Anyone holding the panel's track record on resolved questions can compute it, and publishing the questions, forecasts and outcomes alongside makes it cheap to audit by people and software alike. Model consumers that already average do not need it. Whether it helps people is the open question, and the inflated arm shows the cost of a false one; Appendix B gives the test protocol and Appendix A discusses who should issue such labels.

**Limitations and next steps.** The models answered without retrieval, the questions skew towards politics, crypto and sport, the five-witness pool is a stylised reader (so the premium is an upper bound), and we ran no human participants; Appendix A gives the full list and the dual-use concerns. The next step is the Appendix B experiment, followed by panels with web search, where a shared search engine could make advisors even less independent.

## References

Aitchison, M., Jeen, S., Shevlane, T., & Day, B. (2026). Diversity is the strength of the AI crowd. arXiv:2606.29661.

Baron, J., Mellers, B. A., Tetlock, P. E., Stone, E., & Ungar, L. H. (2014). Two reasons to make aggregated probability forecasts more extreme. Decision Analysis, 11(2), 133–145.

Becker, J., Brackbill, D., & Centola, D. (2017). Network dynamics of social influence in the wisdom of crowds. PNAS, 114(26), E5070–E5076.

Begin, J., Gho, B., Muppavarapu, S., Tsay, T., Mohan, A., Shaik, A., Li, R., Sharma, V., & Vaidheeswaran, A. (2026). Preference optimization drives monoculture in LLM prediction markets. arXiv:2606.26583.

Bommasani, R., Creel, K. A., Kumar, A., Jurafsky, D., & Liang, P. (2022). Picking on the same person: Does algorithmic monoculture lead to outcome homogenization? NeurIPS 2022.

Chuai, Y., Tian, H., Pröllochs, N., & Lenzini, G. (2024). Did the roll-out of Community Notes reduce engagement with misinformation on X/Twitter? Proc. ACM HCI (CSCW).

Clemen, R. T., & Winkler, R. L. (1985). Limits for the precision and value of information from dependent sources. Operations Research, 33(2), 427–442.

Cotton-Barratt, O., & Finnveden, L. (2026). AI for AI for epistemics. Forethought.

Denisov-Blanch, Y., Kazdan, J., Chudnovsky, J., Schaeffer, R., Guan, S., Adeshina, S., & Koyejo, S. (2026). Consensus is not verification: Why crowd wisdom strategies fail for LLM truthfulness. arXiv:2603.06612.

Douven, I. (2026). Wisdom of LLM crowds: Aggregation and contamination in language model ensembles. arXiv:2607.18269.

Goel, S., Struber, J., Auzina, I. A., Chandra, K. K., Kumaraguru, P., Kiela, D., Prabhu, A., Bethge, M., & Geiping, J. (2025). Great models think alike and this undermines AI oversight. ICML 2025. arXiv:2502.04313.

Goldman, A. I. (2001). Experts: Which ones should you trust? Philosophy and Phenomenological Research, 63(1), 85–110.

Halawi, D., Zhang, F., Yueh-Han, C., & Steinhardt, J. (2024). Approaching human-level forecasting with language models. NeurIPS 2024.

Hammond, L., et al. (2025). Multi-agent risks from advanced AI. Cooperative AI Foundation Technical Report.

Huang, J., Li, M., Li, Z., Kwon, S., Yu, H., & Zhang, C. (2026). Counterfactual graph for multi-agent LLM calibration. arXiv:2605.30653.

Hussain, Z., & Nielbo, K. (2026). Conformity mitigations in large language models lie on a single resistance–receptivity frontier. arXiv:2608.11247.

Karger, E., Bastani, H., Yueh-Han, C., Jacobs, Z., Halawi, D., Zhang, F., & Tetlock, P. E. (2025). ForecastBench: A dynamic benchmark of AI forecasting capabilities. ICLR 2025.

Kim, E., Garg, A., Peng, K., & Garg, N. (2025). Correlated errors in large language models. ICML 2025. arXiv:2506.07962.

Kish, L. (1965). Survey Sampling. Wiley.

Kleinberg, J., & Raghavan, M. (2021). Algorithmic monoculture and social welfare. PNAS, 118(22), e2018340118.

Lee, S., & Lee, K. (2026). Multi-agent consensus as a cognitive bias trigger in human–AI interaction. arXiv:2604.22277.

Lorenz, J., Rauhut, H., Schweitzer, F., & Helbing, D. (2011). How social influence can undermine the wisdom of crowd effect. PNAS, 108(22), 9020–9025.

Satopää, V. A., Baron, J., Foster, D. P., Mellers, B. A., Tetlock, P. E., & Ungar, L. H. (2014). Combining multiple probability predictions using a simple logit model. International Journal of Forecasting, 30(2), 344–356.

Schoenegger, P., Tuminauskaite, I., Park, P. S., Bastos, R. V. S., & Tetlock, P. E. (2024). Wisdom of the silicon crowd: LLM ensemble prediction capabilities rival human crowd accuracy. Science Advances, 10(45), eadp1528.

Surowiecki, J. (2004). The Wisdom of Crowds. Doubleday.

Sprint talks (cited as talks): Palermos, S. O. (15 Nov 2026), "Artificial Knowing: AI as Socio-Technical Epistemic Collaboration"; Stray, J. (14 Nov 2026), "Destructive Feedback Loops between Conflict and Knowledge"; Cotton-Barratt, O. (13 Nov 2026), keynote. AI x Epistemics Research Sprint, Apart Research.

\pagebreak

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


## Appendix C. The cost of over-counting, prompts and reproducibility

![Figure C1: Brier score of the plain average (dot) and of the same five advisors read as independent witnesses (arrow tip). Lower is better. Vertical lines mark the human market crowd and always answering 50%.](docs/img/fig3_premium.png){width=5.6}

![Figure C2: AI decision-makers' Brier score relative to the plain panel average, by note. The shaded band is the cost of reading the panel as five independent witnesses.](docs/img/fig5_decisions.png){width=5.2}

**Advisor prompt (system).** "You are a careful forecaster advising someone who has to make a decision. Answer only with JSON: {"p": <probability from 0 to 1 that the question resolves YES>, "why": "<one sentence, at most 30 words>"}." Persona panels prefix "You are a political scientist who studies elections and institutions." (and likewise an economist who works with market and macro data; a superforecaster who starts from base rates and adjusts carefully; an investigative journalist who follows current events closely; a risk analyst whose job is to notice what could go differently than expected). The user message gives the freeze date as today's date, the question, its resolution criteria, background (first 1,500 characters) and closing date.

**Discussion round.** "Your first forecast was p = X. Four other advisors answered the same question: [their p and one-sentence reasons]. Give your final forecast. Change it only if their reasons give you a reason to."

**Shared brief.** gpt-4.1-mini is asked for "a short, neutral research brief for forecasters ... the key considerations, base rates and uncertainties, without giving a final probability" (at most 120 words), which every advisor then reads under "A research assistant prepared this brief for you".

**Decision-maker (system).** "You are helping a person make a decision that depends on whether this question resolves YES. You have asked a panel of five AI advisors. Weigh their answers and give your own final forecast." The four notes are given in Section 3.5.

**Models and settings.** gpt-4.1-mini, gpt-4.1, gpt-4o-mini (temperature 1), gpt-5-mini and gpt-5.4-mini (reasoning effort "low"), via the OpenAI API; Gemma 4 31B and Qwen 3.8 27B via Adaption; Nemotron 3.5 Lightning 30B via NVIDIA. Unparseable answers were re-asked up to twice with a new cache key; panels with any missing answer were dropped (none were dropped in the main OpenAI panels). Each forecast is clipped to [0.01, 0.99] for log-odds. In the unanimity measure a forecast of exactly 0.5 counts as leaning NO.

**Scale and cost.** 13,976 model calls in total (about 7.0 million input and 4.9 million output tokens), including the pilot. The OpenAI panels and decision-maker runs took under an hour; the cross-developer panel ran for most of a day because of rate limits.

**Reproducibility.** `python -m echo.data` builds the question set from the released ForecastBench files; `python -m echo.panels`, `echo.label`, `echo.analyze`, `echo.contrasts`, `echo.decisions` and `echo.figures` regenerate every number and figure. Every model call is stored in `results/cache/` under a hash of the model, messages and sample index, so rerunning the pipeline reads the cache and makes no new calls. Unit tests (`pytest tests`) check the effective-N and conditional-correlation statistics on synthetic panels with known answers.
