Abstract

In clinical settings, nursing records are crucial for patient safety, care quality, and effective
medical team communication. However, severe nurse shortages, especially in hospitals where nurseto-patient ratios often reach 1:10 or even 1:15, substantially increase workloads and documentation
pressure on nursing staff.

To address this, we developed an Automated Nursing Record Generation System that integrates
Natural Language Processing (NLP) and semantic vector retrieval techniques. The system rapidly
retrieves semantically similar historical records, offering editable recommendations structured by the
standardized DART format (Data, Action, Response, Teaching) to streamline documentation and ease
frontline workloads.

Our system combines Flask, PostgreSQL, and Elasticsearch with a Sentence-BERT embedding
model (all-MiniLM-L6-v2) to convert user-entered patient symptoms into semantic vectors. It uses
cosine similarity for real-time retrieval of the most relevant historical records and includes anomaly
detection for physiological data and an interactive interface for easy modification and storage of
records.

Clinical experts evaluated the system's performance, showing high agreement in record selection
(Cohen’s Kappa = 0.73–1.00) and moderate agreement in record ranking (Kendall’s τ = 0.60 -0.73).
These results demonstrate the system's strong clinical applicability and potential as a decision-support
tool.

