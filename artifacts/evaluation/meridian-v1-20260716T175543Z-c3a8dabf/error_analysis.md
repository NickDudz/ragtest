# Representative error analysis

This review uses the completed `meridian-v1-20260716T175543Z-c3a8dabf` run. Cases
were selected from low document recall, low evidence recall, incomplete required
facts, missing or misattributed citations, and answerable-question abstentions.
They are examples of observed behavior, not estimates of population error rates.

## 1. Document-level retrieval miss amid a strong distractor

- **Case:** `q15`, baseline `900/150` ([row 15](per_question.jsonl#L15))
- **Observed:** None of the top five chunks came from `cold_chain_shipping`; the
  top results emphasized sensor calibration and other operational procedures.
  The model correctly abstained from inventing a temperature range, but the
  answerable question received Recall@5 = 0 and fact coverage = 0.
- **Contrast:** Focused `500/80` retrieved the expected source at rank 2 and the
  evidence-bearing chunk by rank 4, then answered `2 to 8 degrees Celsius` with
  the expected citation ([row 45](per_question.jsonl#L45)).
- **Category:** semantic distractor / document retrieval miss.
- **Implication:** Smaller chunks separated the cold-chain rule from surrounding
  material well enough to overcome repeated temperature and calibration terms
  elsewhere in the corpus.

## 2. Correct source, wrong passage

- **Case:** `q17`, focused `500/80` ([row 47](per_question.jsonl#L47))
- **Observed:** `cold_chain_shipping` ranked first, so document Recall@1 = 1, but
  no top-five chunk contained the authored evidence anchor. The answer mentioned
  a temperature excursion and a possible hold, yet omitted the threshold and
  required assessment details; evidence Recall@5 and fact coverage were both 0.
- **Category:** passage miss hidden by document recall.
- **Implication:** Source-level Recall@k alone would call this retrieval a success.
  Passage labels and answer checks expose the lost operational detail.

## 3. Duplicate same-source chunks crowd out a required second source

- **Case:** `q21`, focused `500/80` ([row 51](per_question.jsonl#L51))
- **Observed:** Three of the top four chunks came from `access_control`, while the
  required `incident_response` source never appeared in the top six. The answer
  covered opening an incident and reporting device details, but omitted the
  credential revocation action. Document Recall@5 and citation source recall were
  0.5; fact coverage was 0.
- **Category:** multi-source coverage / rank duplication.
- **Implication:** A future experiment could test source diversification or
  reranking, but V1 deliberately records the failure instead of adding that scope.

## 4. Valid citation syntax points to the wrong document

- **Case:** `q23`, baseline `900/150` ([row 23](per_question.jsonl#L23))
- **Observed:** Both `[S3]` mentions were valid in-range identifiers, producing a
  valid-ID rate of 1.0, but S3 mapped to `fleet_maintenance`, not either expected
  source. Citation source precision and recall were therefore 0 even though the
  prose included the correct three-year retention period.
- **Category:** citation misattribution.
- **Implication:** Citation-format validity is not citation reliability. Mapping
  each marker back to its retrieved source prevents an unsupported groundedness
  claim.

## 5. Multi-source question loses the classification half

- **Case:** `q24`, both configurations ([baseline row 24](per_question.jsonl#L24),
  [focused row 54](per_question.jsonl#L54))
- **Observed:** `remote_site_networking` was retrieved, but `incident_response`
  was absent from the top five in both configurations. The focused answer gave
  the five-minute monitoring trigger but omitted the Severity 1 classification;
  the baseline answer called it a site connectivity incident without supplying
  the required severity. Recall@5 remained 0.5.
- **Category:** cross-document composition failure.
- **Implication:** Improving one-source ranking does not guarantee multi-source
  completeness; this is a persistent failure across the tested chunk geometries.

## 6. Evidence is present but generation abstains

- **Case:** `q13`, focused `500/80` ([row 43](per_question.jsonl#L43))
- **Observed:** `fleet_maintenance` ranked first and the evidence anchor was
  present by rank 3, yet the model said it did not know. Its explanation repeated
  that a site lead cannot authorize the trip and Fleet Operations must be
  contacted, but it failed to state the policy conclusion: no ordinary trip may
  be authorized and the vehicle remains out of service. Citation presence and
  fact coverage were 0.
- **Category:** generation failure after successful retrieval.
- **Implication:** Retrieval success must be reported separately from answer
  quality; this case would be invisible in retrieval-only metrics.

## 7. Deterministic checks have known blind spots

- **Fact-matching case:** For `q04`, the baseline answer correctly said the Tier 1
  RPO was 30 minutes, but the authored phrase alternatives did not match that
  exact word order, so one correct fact was scored false ([row 4](per_question.jsonl#L4)).
- **Citation-format case:** Correct abstentions such as `q26` appended ranges like
  `[S1-S5]` ([baseline row 26](per_question.jsonl#L26), [focused row 56](per_question.jsonl#L56)).
  The documented parser recognizes individual `[S#]` markers, not ranges, so
  those strings do not count as citations even though a reader may interpret
  them that way.
- **Category:** evaluator proxy limitation.
- **Implication:** Required-fact coverage can under-credit paraphrases, and the
  citation parser can miss nonconforming citation syntax. Both metrics remain
  useful because their rules are deterministic and auditable, but neither is a
  semantic judge.

## Prioritized follow-up experiments

1. Add source-diversified retrieval as one controlled experiment to address
   multi-source crowding (`q21`, `q23`, `q24`).
2. Test a compact evidence-focused context assembly strategy for cases where the
   source is retrieved but the evidence passage is not (`q04`, `q08`, `q17`).
3. Expand citation parsing to detect and separately flag ranges rather than
   silently treating them as absent.
4. Review required-fact alternative authoring with a second human pass before
   treating the lexical proxy as a portfolio headline.

These are follow-up hypotheses, not V1 results. No reranker, diversification
step, semantic judge, or metric rule was retrofitted after observing this run.
