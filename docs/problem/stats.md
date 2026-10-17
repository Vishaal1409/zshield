# ZShield: India Fraud and Scale Statistics

All pages were opened on 2026-10-17 (access date). Quotes are copied from the page text. Units are as the source states them.

Note on how pages were opened: pib.gov.in and mha.gov.in returned 403 to the WebFetch tool, so these were fetched with `curl` and the text read directly. The RBI Trend and Progress PDF was behind a human-verification page and was not used. Lead re-check (17 Oct 2026): every figure and quote below was re-fetched with curl and found verbatim on its page, including the PIB and MHA pages and the MHA PDF. The release date of the RBI Annual Report (29 May 2025) is not printed on the web page itself; confirm it from the RBI press release before quoting the date.

---

## Stat 1: RBI, bank fraud cases, card/internet category

- **Figure.** Card/Internet frauds, 2024-25: 13,516 cases (56.5% of all frauds by number), amount involved ₹520 crore (1.4% of amount). In 2023-24: 29,082 cases (80.6%), ₹1,457 crore (11.9%).
- **Exact quote.** "Frauds have occurred predominantly in the category of digital payments (card/internet) in terms of number and primarily in the loan portfolio (advances) in terms of value (Table VI.3)." Table VI.3 row: "Card/Internet 6,699 278 29,082 1,457 13,516 520 (49.7) (1.5) (80.6) (11.9) (56.5) (1.4)" (columns: 2022-23, 2023-24, 2024-25; number, then amount in ₹ crore). Total row: "13,494 18,981 36,060 12,230 23,953 36,014".
- **Publisher / report.** Reserve Bank of India, Annual Report 2024-25, Chapter VI "Regulation, Supervision and Financial Stability", paragraph VI.61, Tables VI.2 and VI.3.
- **Published.** 29 May 2025.
- **URL.** https://rbi.org.in/scripts/AnnualReportPublications.aspx?Id=1436
- **Accessed.** 2026-10-17
- **Use in deck.** Shows that by number of cases, card/internet is the main fraud category in bank reporting, while the value is much smaller than in loans. Supports "many small, fast cases that need automated scoring".
- **Caution.** RBI reports by date of reporting, and the table is by "Area of Operation". Do not call these "losses".

## Stat 2: RBI discussion paper, digital payment frauds reported on NCRP

- **Figure.** 2025: 28 lakh frauds reported, value ₹22,931 crore (from 2.6 lakh and ₹551 crore in 2021).
- **Exact quote.** "Figures from the National Cyber Crime Reporting Portal (NCRP) indicate that frauds related to digital payments are on the rise." Table: "2021 2.6 lakh 551; 2022 6.9 lakh 2,290; 2023 13.1 lakh 7,465; 2024 24 lakh 22,848; 2025 28 lakh 22,931" (value in ₹ Crore).
- **Speed / irreversibility quotes (same page).** "Given the instantaneous nature of payments through systems such as NEFT, RTGS, UPI and IMPS, the scope for timely intervention and recovery of funds becomes limited." And: "funds can be transferred instantaneously by customers (victims) with minimal effort before realising that they are being duped. Post-transaction remedies to recover such funds being limited, a defrauded user is often left with a few remedies and uncertain outcomes, which are time-consuming and show low recovery rates."
- **Publisher / report.** Reserve Bank of India, "Discussion Paper - Exploring safeguards in digital payments to curb frauds".
- **Published.** 9 Apr 2026.
- **URL.** https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23810
- **Accessed.** 2026-10-17
- **Use in deck.** Opener, plus the "why alerts after the fact fail" slide. The same paper also mentions a "risk score generated on a real-time, transaction-by-transaction basis, even before the transaction is executed", which matches ZShield's approach.

## Stat 3: MHA, cyber fraud losses reported by citizens, 2022 to 2024

- **Figure.** 2024: ₹22,845.73 crore reported (2023: ₹7,465.18 crore; 2022: ₹2,290.24 crore). Incidents on NCRP in 2024: 2,268,346.
- **Exact quote.** "total amount of losses incurred by citizens due to cyber frauds in the entire country including Bihar from the year 2022 to 2024 are as under: Year Amount Reported (₹ In Crore) 2022 2290.24 2023 7465.18 2024 22845.73". Incidents table row: "3 2024 2268346 42.08%".
- **Publisher / report.** Ministry of Home Affairs, Lok Sabha Unstarred Question No. 432 "Cases of Cybercrime", written answer by Shri Bandi Sanjay Kumar, MoS Home Affairs.
- **Published.** Answered 2 Dec 2025.
- **URL.** https://www.mha.gov.in/MHA1/Par2017/pdfs/par2025-pdfs/LS02122025/432.pdf
- **Accessed.** 2026-10-17
- **Use in deck.** Shows the three-fold jump from 2023 to 2024 in reported amounts.
- **Note.** A PIB release of 2 Apr 2025 (https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2117716&reg=48&lang=2, Release ID 2117716) says: "total number of complaints on NCRP and amount lost were 19.18 lakh and 22811.95 crore respectively in 2024." This is a different cut of the data (complaints vs incidents). Do not mix the two numbers on one slide.

## Stat 4: PIB / MHA, five-year complaints, amount reported, and amount saved

- **Figure.** 2021 to 2025: more than 6,589,201 financial fraud complaints on NCRP; more than ₹55,050 crore reported. Amount saved through CFCFRMS: more than ₹11,158 crore in more than 32.80 lakh complaints, till 30.06.2026.
- **Exact quote.** "As per CFCFRMS operated by I4C, till 30.06.2026, financial amount of more than Rs. 11,158 Crore has been saved in more than 32.80 lakh complaints." And: "from the year 2021 to 2025, the total number of financial frauds complaints on NCRP are more than 6589201, the total amount reported is more than ₹ 55050 Crores, the total amount marked as Lien is more than ₹ 8189 Crores and the number of FIRs registered is more than 195760."
- **Publisher / report.** PIB, Ministry of Home Affairs, "National Cyber Crime Data" (Lok Sabha written reply by MoS Shri Bandi Sanjay Kumar).
- **Published.** 21 Jul 2026.
- **URL.** https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287039&reg=48&lang=2 (Release ID 2287039)
- **Accessed.** 2026-10-17
- **Use in deck.** The recovery side: reporting and freezing after the fact saves part of the money, which argues for stopping it before settlement. Earlier figure from the Dec 2025 reply: "more than Rs. 7,130 Crore has been saved in more than 23.02 lakh complaints".
- **Caution.** The "reported" figure covers 2021 to 2025, while "saved" runs till 30.06.2026 and counts complaints through CFCFRMS. Do not present one divided by the other as a recovery rate.

## Stat 5: PIB / NPCI, UPI scale

- **Figure.** July 2026: 2,366 crore transactions in the month; ₹29.88 lakh crore monthly value. FY 2025-26: over 24,162 crore transactions, approximately ₹314 lakh crore.
- **Exact quote.** "Record Monthly Volume (July 2026) 2,366 Crore Record Monthly Value (July 2026) ₹29.88 Lakh Crore" and "July 2026 recording 2,366 crore transactions, the highest monthly transaction volume in UPI's decade-long journey." Also "Daily Average Transactions (2026) 66 Crore".
- **Publisher / report.** PIB, "UPI Completes 10 Years of Digital Payments Revolution- Globally Recognised as World's Largest Real-Time Payment System" (key statistics attributed to NPCI).
- **Published.** 24 Aug 2026.
- **URL.** https://www.pib.gov.in/PressReleasePage.aspx?PRID=2302657&reg=48&lang=2 (Release ID 2302657)
- **Accessed.** 2026-10-17
- **Use in deck.** Scale: a scorer must keep up with this volume. Fits the IBM Z / LinuxONE throughput angle (use "designed for", not a benchmark claim).
- **Note.** The NPCI product-statistics page itself did not return data to the fetch tool, so the NPCI figure is cited through PIB.

---

## Opening line pick

**Pick: Stat 2 (RBI discussion paper, 9 Apr 2026).** It is the regulator's own text, the most recent source, and it names both the scale and the core problem (instant payments, little scope to recover).

Draft opening sentence:

> "In 2025, 28 lakh digital payment frauds were reported on the National Cyber Crime Reporting Portal, worth ₹22,931 crore, and the Reserve Bank says that, because payments are instantaneous, 'the scope for timely intervention and recovery of funds becomes limited'."

Say "reported", not "lost". The RBI paper calls the column "Value of frauds (in ₹ Crore)".

## UNVERIFIED (do not use)

- RBI Report on Trend and Progress of Banking in India 2024-25: PDF not opened (human-verification page). The RBI Annual Report 2024-25 (stat 1) was used instead.
- NPCI UPI product-statistics page (npci.org.in): returned no data to the fetch tool. UPI figures come via PIB only.
- Any figure from news sites (The420, Inc42, The Week, factly, Shankar IAS) seen in search results. These were pointers only and were not used.
- "Only about 3% of complaints became FIRs": from a news report, not verified. (From the PIB figures above, 195,760 FIRs against 6,589,201 complaints would be about 3%, but that is our arithmetic and is not a source statement; do not put it in the deck as a sourced figure.)

## Caveats

- RBI fraud data is by date of reporting, not date of occurrence. Cases reported in a year may have happened earlier. The 2024-25 amount was inflated by reclassification: "removal of fraud classification in 122 cases amounting to ₹18,674 crore reported during previous financial years". RBI also notes the data covers frauds of ₹1 lakh and above and the amount involved is not the same as actual loss.
- NCRP numbers are complaints or reported incidents, not confirmed fraud. Amounts are "reported" by complainants.
- Different government releases give different 2024 numbers (22,845.73, 22,811.95 and 22,848 crore) because they use different cuts and dates. Quote each one with its own source.
- "Saved" amounts and "reported" amounts cover different periods and bases. Do not compute a recovery rate.
- Units: lakh = 100,000; crore = 10 million. Keep the source's units on slides.
