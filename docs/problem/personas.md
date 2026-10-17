# ZShield Personas

**All three personas are illustrative composites. They are not real people. The quotes are illustrative, not real statements.**

---

## Persona 1: Meera, bank fraud analyst (illustrative composite)

**Profile.** Works in a bank's fraud operations team. Reviews a queue of alerts every shift.

**Goal.** Catch real fraud quickly and let honest customers through.

**Pain point.** The queue is full of false alerts. Each alert shows a score but little reason, so every case needs manual digging. Real cases wait behind noise.

**What ZShield changes.** Only the riskiest payments reach her as HOLD. Each one comes with the top 3 reasons (rule-based today; SHAP when the model lands) and a short plain-language alert. She can approve, block or escalate (API built; dashboard buttons pending), and her action is logged. The AI explains; she decides.

> "I don't need a number. I need to know why this one is different." (illustrative quote, not a real person)

**Demo story.** All three stories, ending with the Block click.

---

## Persona 2: Kamla, first-time UPI user, age 68 (illustrative composite)

**Profile.** Retired. Started using UPI recently, with help from a family member. Trusts calls that sound official.

**Goal.** Pay bills and send money to family without trouble.

**Pain point.** She does not know who to call when a message or call sounds urgent. A caller who sounds official can pressure her into sending money fast. By the time she tells anyone, the payment has settled.

**What ZShield changes.** If a call pushes her to send her whole balance to a brand-new recipient at 2 AM, that payment is held before settlement. Where a lighter check is enough, the step-up gives her a pause and a plain warning. Her ordinary payments still go through in milliseconds.

> "I only wanted to do what the officer told me. I didn't know who else to ask." (illustrative quote, not a real person)

**Demo story.** Scam Drain (also Normal Day, to show honest payments pass).

---

## Persona 3: "The Caller", the adversary (illustrative composite)

This persona exists only to show what ZShield is designed to stop. It is described at the level of publicly known scam patterns. It is not a method.

**Profile.** A scammer who targets people like Kamla. Publicly reported patterns include posing as an officer or bank/KYC official, or as a relative in trouble, and creating urgency and fear. The Government of India has warned about one such pattern, the "digital arrest" scam, in a PIB alert (see below). Stolen money is then moved on through other accounts, often called mule accounts.

**Goal.** Get the victim to send as much money as possible, as fast as possible.

**What they rely on.**
- Speed: the victim acts under pressure, before thinking.
- Irreversibility: instant payments are hard to recover. The RBI paper says "the scope for timely intervention and recovery of funds becomes limited".
- Late alerts: warnings that arrive after settlement.
- Victims who do not know who to call.

**What ZShield changes for them.**
- The drain payment is held before settlement.
- The step-up check gives the victim a pause and a plain warning.
- The mule-burst pattern (one receiving account suddenly getting many transfers) is flagged.
- An analyst sees the reasons and can block.

> "If they just send it quickly, nobody can stop it." (illustrative quote, not a real person)

**Demo story.** Scam Drain and Mule Burst.

**Official reference (verified).** PIB (Ministry of Home Affairs), "Alert against incidents of 'Blackmail' and 'Digital Arrest' by Cyber Criminals Impersonating State/UT Police, NCB, CBI, RBI and other Law Enforcement Agencies", posted 14 May 2024: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2020570 (accessed 2026-10-17). It says the fraudsters "typically call a potential victim" and that citizens should "immediately report the incident on cybercrime helpline number 1930 or www.cybercrime.gov.in". It also says I4C is "facilitating blocking of SIM cards, Mobile devices and Mule accounts used by such fraudsters."
