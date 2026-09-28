# Verified literature map

Records below were checked against ACL Anthology `.bib` pages, TACL/DOI pages, NeurIPS proceedings, or PMLR. Status: **must cite**, **likely cite**, or **background**.

## Bucket A. Automated fact verification / FEVER

| Paper | Venue | Open PDF | Why it matters | Section | Status |
|---|---|---|---|---|---|
| Thorne et al. 2018. FEVER. NAACL. DOI 10.18653/v1/N18-1074 | NAACL 2018 | https://aclanthology.org/N18-1074.pdf | Dataset, gold evidence pointers, Supported/Refuted/NEI | Design, Intro | must |
| Thorne et al. 2018. FEVER Shared Task. FEVER workshop. DOI 10.18653/v1/W18-5501 | FEVER 2018 | https://aclanthology.org/W18-5501.pdf | Retrieval + verification already hard on Wikipedia | Related 2.1 | likely |
| Wadden et al. 2020. SciFact. EMNLP. DOI 10.18653/v1/2020.emnlp-main.609 | EMNLP 2020 | https://aclanthology.org/2020.emnlp-main.609.pdf | Scientific-claim extension of the FEVER recipe | Related 2.1 | likely |
| Aly et al. 2021. FEVEROUS. NeurIPS D&B | NeurIPS 2021 | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/68d30a9594728bc39aa24be94b319d21-Paper-round1.pdf | Sentence + table evidence; we stay on sentence gold | Related 2.1 | likely |
| Jiang et al. 2020. HoVer. EMNLP Findings. DOI 10.18653/v1/2020.findings-emnlp.309 | EMNLP Findings 2020 | https://aclanthology.org/2020.findings-emnlp.309.pdf | Many-hop Wikipedia verification | Related 2.1 | background |
| Schuster et al. 2019. Towards Debiasing Fact Verification. EMNLP. DOI 10.18653/v1/D19-1341 | EMNLP 2019 | https://aclanthology.org/D19-1341.pdf | Claim-only artifacts without evidence | Related 2.1 | likely |
| Guo, Schlichtkrull, Vlachos 2022. Survey on Automated Fact-Checking. TACL 10:178–206. DOI 10.1162/tacl_a_00454 | TACL 2022 | https://aclanthology.org/2022.tacl-1.11.pdf | Positions claim detection / retrieval / verification | Related 2.1 | must |
| Mamta and Cocarascu 2025. FactEval. NAACL. DOI 10.18653/v1/2025.naacl-long.534 | NAACL 2025 | https://aclanthology.org/2025.naacl-long.534.pdf | LLM FV brittleness on FEVER under perturbations | Related 2.2, Disc. | must |

## Bucket B. Evidence sufficiency and ambiguity

| Paper | Venue | Open PDF | Why it matters | Section | Status |
|---|---|---|---|---|---|
| Atanasova et al. 2022. Fact Checking with Insufficient Evidence. TACL 10:746–763. DOI 10.1162/tacl_a_00486 | TACL 2022 | https://aclanthology.org/2022.tacl-1.43.pdf | Sufficiency is not guaranteed even when evidence is present | Related 2.3 | must |
| Glockner et al. 2024. AmbiFC. TACL 12:1–18. DOI 10.1162/tacl_a_00629 | TACL 2024 | https://aclanthology.org/2024.tacl-1.1.pdf | Ambiguous claim–evidence pairs; soft labels | Related 2.3, residual amb. | must |
| Schuster et al. 2021. VitaminC. NAACL. DOI 10.18653/v1/2021.naacl-main.52 | NAACL 2021 | https://aclanthology.org/2021.naacl-main.52.pdf | Contrastive evidence revisions change labels | Related 2.1 | likely |

## Bucket C. LLM factuality / evidence robustness

| Paper | Venue | Open PDF | Why it matters | Section | Status |
|---|---|---|---|---|---|
| Wan, Wallace, Klein 2024. What Evidence Do LMs Find Convincing? ACL. DOI 10.18653/v1/2024.acl-long.403 | ACL 2024 | https://aclanthology.org/2024.acl-long.403.pdf | Models overweight relevance vs human credibility cues | Related 2.2 | must |
| Longpre et al. 2021. Entity-Based Knowledge Conflicts. EMNLP. DOI 10.18653/v1/2021.emnlp-main.565 | EMNLP 2021 | https://aclanthology.org/2021.emnlp-main.565.pdf | Parametric vs contextual conflict | Related 2.2 | must |
| Liu et al. 2024. Lost in the Middle. TACL 12:157–173. DOI 10.1162/tacl_a_00638 | TACL 2024 | https://aclanthology.org/2024.tacl-1.9.pdf | Representation/position of evidence changes use | Related 2.2, representation | likely |
| Shi et al. 2023. LLMs Can Be Easily Distracted by Irrelevant Context. ICML / PMLR 202:31210–31227 | ICML 2023 | https://proceedings.mlr.press/v202/shi23a/shi23a.pdf | Extra context can degrade decisions | Related 2.2 | likely |

## Bucket D. LLM-as-judge reliability

| Paper | Venue | Open PDF | Why it matters | Section | Status |
|---|---|---|---|---|---|
| Zheng et al. 2023. Judging LLM-as-a-Judge. NeurIPS D&B | NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/file/91f18a1287b398d378ef22505bf41832-Paper-Datasets_and_Benchmarks.pdf | Foundational judge protocol; position/verbosity biases | Related 2.4 | must |
| Liu et al. 2023. G-Eval. EMNLP. DOI 10.18653/v1/2023.emnlp-main.153 | EMNLP 2023 | https://aclanthology.org/2023.emnlp-main.153.pdf | LLM evaluators; self-preference risk | Related 2.4 | must |
| Chen et al. 2024. Humans or LLMs as the Judge? EMNLP. DOI 10.18653/v1/2024.emnlp-main.474 | EMNLP 2024 | https://aclanthology.org/2024.emnlp-main.474.pdf | Systematic judge biases | Related 2.4 | must |
| Huang et al. 2025. Empirical Study of LLM-as-a-Judge. ACL Findings. DOI 10.18653/v1/2025.findings-acl.306 | ACL Findings 2025 | https://aclanthology.org/2025.findings-acl.306.pdf | Judge family is not interchangeable | Related 2.4, Disc. 5.4 | must |
| Shi et al. 2025. Judging the Judges. IJCNLP-AACL. DOI 10.18653/v1/2025.ijcnlp-long.18 | IJCNLP-AACL 2025 | https://aclanthology.org/2025.ijcnlp-long.18.pdf | Position bias varies by judge and task | Related 2.4 | likely |

**Count:** 20 verified records, all cited in Related Work or Discussion. Remaining optional items stay in `CITATION_TODOS.md`.
