# Data methodology (one page for the deck)

**Source.** PaySim: 6.36 million synthetic mobile-money transactions over 743 hourly steps (about 31 days),
with 8,213 frauds (0.13%). It is synthetic, so it holds no real personal data. Details: `features/data_card.md`.

**What the data shows** (`docs/eda/`)
- Fraud happens **only** in TRANSFER and CASH_OUT, so we score only those two types.
- 97.7% of frauds **empty the account** in one move.
- **Night is risky:** at hour 5 the fraud rate is 22%, against 0.07% at noon.
- Fraud amounts are larger, and capped at 10 million by the simulator.

**Features from the moment of payment only.** Balance mismatch at the sender and the recipient, full-drain flag,
amount-to-balance ratio, hour of day, and type. For rules and explanations we add new recipient, sender velocity
and recipient inbound count over the last 6 hours. **One function builds features for both training and the live API**,
and a test proves they produce identical values, so the model sees in production exactly what it saw in training.

**Honest split: by time, never random.** Train steps 1 to 500, validate 501 to 620, test 621 to 743.
We train on the past and test on the future, like a real bank.

**Imbalance.** Fraud is 0.13% of rows, so accuracy is meaningless (always saying "legit" scores 99.87%).
We report PR-AUC and recall at a fixed false-positive rate, and compare against a logistic-regression baseline.

**No leakage.** The label columns (`isFraud`, and `isFlaggedFraud`, which is PaySim's own rule output) are never
used as features. A test checks that no future payment changes a past payment's features.

**Limits we state openly**
- **PaySim is easy.** One raw balance field alone separates fraud at 0.94 AUC, because of how the simulator writes
  balances. Our near-perfect test score reflects that, and real bank data would score lower.
- **No account history:** 99.85% of senders appear once. The Mule Burst demo is therefore synthetic, and labelled as such.
- **Shifting volume:** activity drops sharply after step 400, so later periods are fraud-heavy.
- **No demographic fields,** so fairness across customer groups cannot be measured on this dataset.
