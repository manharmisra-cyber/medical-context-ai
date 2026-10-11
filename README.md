# Medical Context AI

**An open-source research project exploring evidence-based medical information integration, knowledge graphs, and transparent clinical reasoning.**

> **Research prototype. Not for clinical use. Not a validated diagnostic system or medical device.**

Medical Context AI explores how medical knowledge from different sources can be organized, connected, and analyzed to investigate relationships between clinical findings and diseases.

The project currently integrates disease terminology from MONDO, phenotype information from the Human Phenotype Ontology (HPO), and access to the World Health Organization's ICD-11 API.

An experimental reasoning engine evaluates multiple findings together and produces explainable disease-association results based on available annotations.

**Current version:** `0.0.2.5`  
**Development stage:** Stage 2.5 — Medical knowledge integration and interactive CLI  
**MONDO dataset version:** `v2026-10-06`  
**Status:** Functional research prototype with known limitations  
**License:** MIT

---

## Vision

Medical information is distributed across multiple sources, including symptoms, laboratory results, imaging findings, patient history, and clinical observations.

Medical Context AI investigates whether structured knowledge representation and transparent reasoning methods can help organize this information and identify relationships between findings and possible medical conditions.

The long-term research objectives include:

- Representing diseases, symptoms, laboratory abnormalities, and other clinical findings in a unified knowledge structure.
- Combining information from multiple medical knowledge sources.
- Preserving the provenance of medical associations and mappings.
- Evaluating multiple findings together rather than independently.
- Explaining which findings support or conflict with a hypothesis.
- Representing missing information, ambiguity, and uncertainty.
- Investigating which additional information could improve an analysis.
- Evaluating reasoning approaches against appropriate research benchmarks.
- Exploring future integration with medical imaging and other modalities.

These are research objectives, not claims of demonstrated clinical effectiveness.

---

## Current Implementation — v0.0.2.5

Medical Context AI has progressed beyond its initial knowledge-graph foundation.

### 1. Medical Knowledge Graph

The project includes a custom Python knowledge-graph implementation with support for:

- Structured medical nodes and relationships.
- Disease concepts imported from MONDO.
- Disease hierarchy relationships.
- External identifiers and metadata.
- Graph queries and basic validation.

The graph provides a foundation for connecting medical information from multiple sources.

### 2. MONDO Disease Ontology

The MONDO importer processes the downloaded ontology and extracts:

- Disease identifiers.
- Disease names.
- Disease hierarchy relationships.
- External cross-references.
- Associated metadata.

MONDO provides a shared disease terminology for the research system.

**Current limitation:** Not all disease concepts can be reliably connected to records in other medical datasets.

### 3. Human Phenotype Ontology (HPO)

The HPO integration uses two datasets:

**`phenotype.hpoa`**

Provides disease-to-phenotype associations, including links between disease identifiers and HPO terms.

**`hp.obo`**

Provides phenotype terminology, including:

- HPO identifiers.
- Human-readable phenotype names.
- Synonyms.
- Searchable terminology.

HPO phenotypes include patient-reported symptoms, clinical signs, anatomical abnormalities, laboratory findings, and developmental abnormalities.

The system supports searching phenotype terminology using ordinary text or HPO identifiers.

**Current limitation:** HPO disease annotations are incomplete and emphasize rare and genetic diseases. Many common conditions do not have sufficient associations for the current reasoning system.

### 4. ICD-11 Integration

The project includes an ICD-11 client using the World Health Organization API.

Implemented capabilities include:

- OAuth2 authentication.
- Searching WHO ICD-11 Foundation entities.
- Retrieving entity information.
- Accessing disease classification metadata.
- Supporting manually approved disease-identity mappings.

The interactive disease lookup can optionally search ICD-11 for additional information.

**Current limitation:** ICD-11 search results are not automatically treated as verified MONDO mappings. Full ICD-11 integration into the unified disease graph remains incomplete.

### 5. Disease Identity Resolution

An experimental identity resolver connects disease identifiers across medical sources.

It supports:

- Normalizing external identifiers.
- Identifying candidate MONDO mappings from ontology cross-references.
- Detecting ambiguous mappings.
- Recording explicitly approved mappings.
- Avoiding automatic approval of uncertain identity relationships.

**Known issue:** Some HPO disease identifiers cannot be resolved to MONDO identifiers. Consequently, some results display their original OMIM or Orphanet identifiers rather than a verified MONDO identifier.

A candidate mapping does not establish exact disease equivalence.

### 6. Experimental Reasoning Engine

The current reasoning engine accepts multiple HPO findings together and compares them against available disease-phenotype associations.

Results are classified according to the proportion of entered findings that appear in each disease's recorded annotations.

| Classification | Annotation Coverage |
|---|---|
| **MATCH** | 100% of entered findings |
| **PARTIAL MATCH** | More than 50%, but less than 100% |
| **IRRELEVANT (hidden)** | 50% or fewer |

The engine also supports recording confirmed absent findings and calculating an experimental heuristic score.

Results are ordered by annotation coverage and heuristic score.

**Important:** These classifications describe matches against available dataset annotations. They are not diagnoses, probabilities, measures of clinical likelihood, or medically validated exclusion criteria.

Missing annotations do not establish that a disease is incompatible with a patient's findings.

### 7. Interactive Command-Line Interface

Version `0.0.2.5` introduces an interactive CLI for exploring the integrated datasets.

The main menu provides:

#### Option 1 — Disease to Symptoms and Information

- Search MONDO diseases by name or identifier.
- Select a matching disease.
- Display available disease metadata and external identifiers.
- View potential HPO phenotype associations using readable names.
- Optionally search WHO ICD-11 for additional classification information.

#### Option 2 — Symptoms/Information to Diseases

- Enter multiple findings as comma-separated text.
- Search HPO terminology using names and synonyms.
- Select the intended HPO terms when searches are ambiguous.
- Optionally specify confirmed absent findings.
- Evaluate all selected findings together.
- Display full and partial annotation matches.
- Show disease identifiers, candidate names, supporting findings, coverage, and heuristic scores.

The CLI is intended for dataset exploration and research demonstrations, not clinical decision-making.

---

## Current Architecture

```text
                  MEDICAL CONTEXT AI
                       v0.0.2.5

                   Interactive CLI
                          |
             +------------+------------+
             |                         |
      Disease Lookup             Finding Lookup
             |                         |
             v                         v
       MONDO Search              HPO Term Search
             |                         |
             v                         v
       Disease Identity          Patient Evidence
             |                         |
             |                         v
             |                  Phenotype Ranking
             |                         |
             +------------+------------+
                          |
                          v
                  Research Results
                          |
               +----------+----------+
               |                     |
          MONDO / HPO           ICD-11 Search
          Information           (where requested)
```

The current implementation consists of independently testable knowledge, identity-resolution, terminology, and reasoning components.

Future versions may introduce additional clinical evidence sources, improved reasoning methods, and structured evaluation.

---

## Development Roadmap

The project uses incremental development milestones.

| Version / Stage | Objective | Status |
|---|---|---|
| `0.0.1` | Project foundation, schemas, and initial knowledge graph | Completed |
| Stage 2.2 | HPO disease-phenotype association importer | Implemented |
| Stage 2.3 | ICD-11 WHO API client | Implemented |
| Stage 2.4 | MONDO ontology importer and graph integration | Implemented |
| **`0.0.2.5` / Stage 2.5** | Identity resolution, phenotype ranking, HPO terminology, interactive CLI | **Current prototype** |
| Stage 2.6 | Research training experiments, feedback mechanisms, and evaluation | Planned |
| `0.1.0` | More complete queryable knowledge graph and improved evidence matching | Planned |
| `0.2.0` | Structured fictional cases and reasoning explanations | Planned |
| `0.3.0` | Baseline comparisons and automated evaluation | Planned |
| `0.4.0+` | Uncertainty, multimodal evidence integration, and information selection | Planned |
| Future | Validated research datasets, model integrations, and extended evaluation | Exploratory |

Milestone definitions may evolve as the project develops.

Stage 2.5 is considered a functional prototype milestone, not a declaration that medical data integration is complete.

---

## Technology Stack

The current implementation uses:

- **Python 3** for the knowledge graph, data importers, CLI, and reasoning components.
- **JSON** for ontology and structured medical data.
- **OBO** for HPO terminology.
- **HPOA** for disease-phenotype associations.
- **WHO ICD API** for ICD-11 entity searches and retrieval.
- **OAuth2** for WHO API authentication.
- **Python `unittest`** for automated testing.
- **Git and GitHub** for version control and issue tracking.

The initial system does not require a GPU.

Machine-learning libraries and additional infrastructure will be introduced only where justified by research objectives.

---

## Repository Structure

```text
medical-context-ai/
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml
├── docs/
├── configs/
├── data/
│   └── external/
│       ├── mondo.json
│       ├── phenotype.hpoa
│       └── hp.obo
├── src/
│   └── medical_context_ai/
│       ├── knowledge/
│       │   ├── schema.py
│       │   ├── graph.py
│       │   ├── mondo_importer.py
│       │   ├── hpo_importer.py
│       │   ├── hpo_terms.py
│       │   ├── icd_client.py
│       │   ├── icd_integration.py
│       │   └── identity.py
│       ├── reasoning/
│       │   ├── evidence.py
│       │   └── ranking.py
│       └── scripts/
│           ├── medical_cli.py
│           ├── medical_data.py
│           ├── disease_lookup.py
│           ├── symptom_lookup.py
│           ├── test_mondo_import.py
│           ├── test_icd_connection.py
│           └── test_identity_integration.py
└── tests/
    ├── test_graph.py
    ├── test_mondo_importer.py
    ├── test_icd_integration.py
    ├── test_ranking.py
    └── test_coverage_ranking.py
```

The structure above reflects the Stage 2.5 development plan. Some supporting directories or test files may differ between environments.

Downloaded external datasets are stored locally and should not be committed without checking redistribution permissions.

---

## Getting Started

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd medical-context-ai
```

Replace `<repository-url>` with the GitHub repository URL.

### 2. Create a Virtual Environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the Project

```powershell
python -m pip install -e .
```

### 4. Download the Required Datasets

The CLI expects the following files inside `data/external/`:

| File | Source |
|---|---|
| `mondo.json` | MONDO ontology |
| `phenotype.hpoa` | Human Phenotype Ontology disease annotations |
| `hp.obo` | Human Phenotype Ontology terminology |

Official sources:

- MONDO: https://mondo.monarchinitiative.org/
- HPO: https://hpo.jax.org/
- HPO repository: https://github.com/obophenotype/human-phenotype-ontology

The files must be available at the expected paths before running the CLI.

ICD-11 functionality requires valid WHO API credentials, configured locally according to the ICD client implementation.

Never commit credentials or access tokens.

### 5. Run Automated Tests

```powershell
python -m unittest discover -s tests -v
```

The test suite covers graph functionality, ontology importers, ICD integration, and experimental ranking behavior.

A successful test run does not establish medical accuracy or clinical validity.

### 6. Launch the Interactive CLI

```powershell
python -m medical_context_ai.scripts.medical_cli
```

The program displays:

```text
=============================================
         MEDICAL CONTEXT AI
              STAGE 2.5
=============================================

1. Disease to symptoms and information
2. Symptoms/information to diseases
0. Exit

Select option:
```

### 7. Example Research Queries

#### Disease Lookup

```text
Select option: 1
Disease name or MONDO ID: influenza
```

This searches the MONDO disease terminology.

Available phenotype associations depend on successful identity resolution and dataset coverage.

#### Finding Lookup

```text
Select option: 2
Present findings: fever, headache, seizures
```

The system resolves the entered terms to HPO concepts and compares them together against recorded disease-phenotype associations.

The resulting rankings are experimental annotation comparisons, not clinical diagnoses.

---

## Known Issues and Limitations

Version `0.0.2.5` has several documented limitations.

### 1. Incomplete MONDO–HPO Identity Resolution

Not all disease identifiers in HPO associations resolve to unique MONDO identifiers.

This can result in:

- Missing disease names.
- Original OMIM or Orphanet identifiers appearing in results.
- Ambiguous disease mappings.
- Incomplete integration between datasets.

**Planned improvement:** Import and evaluate authoritative mapping files while preserving mapping semantics and provenance.

### 2. Incomplete Disease Coverage

Medical datasets differ significantly in scope.

For example:

- MONDO contains disease concepts that may have no corresponding HPO annotations.
- HPO disease associations emphasize rare and genetic diseases.
- Common conditions such as influenza may not be adequately represented in the current phenotype-ranking dataset.
- ICD-11 classifications do not provide a complete replacement for disease-phenotype associations.

**Planned improvement:** Evaluate additional curated evidence sources, particularly for common diseases.

### 3. Simplified Matching Algorithm

The current reasoning engine uses annotation coverage and heuristic scores.

It does not yet adequately model:

- Disease prevalence or prior probabilities.
- Symptom frequency and specificity.
- Age-dependent presentations.
- Symptom duration and progression.
- Clinical severity.
- Relationships between correlated findings.
- Missing or incomplete annotations.
- Comprehensive negative evidence.

A 100% annotation match does not establish that a disease is likely, and a low annotation match does not exclude it.

### 4. Limited Natural-Language Understanding

The CLI supports free-text terminology lookup using HPO names and synonyms.

It does not yet provide reliable interpretation of complete clinical narratives, temporal descriptions, negation in free text, or complex medical context.

### 5. Incomplete ICD-11 Integration

ICD-11 API access is implemented, but automatic verified linking between ICD-11 entities and MONDO concepts remains incomplete.

Search-result similarity must not be treated as proof of disease equivalence.

### 6. No Clinical Validation

The project has not established diagnostic accuracy, sensitivity, specificity, calibration, or safety through appropriate clinical evaluation.

Current unit tests verify software behavior, not clinical performance.

These limitations will be tracked and addressed through GitHub Issues and future development milestones.

---

## Data and Research Principles

Medical Context AI prioritizes:

1. **Traceable knowledge:** Preserve the origin of imported disease and phenotype information.
2. **Verified identity mappings:** Distinguish exact equivalence from broader, narrower, related, or ambiguous relationships.
3. **Transparent reasoning:** Make supporting evidence and scoring rules inspectable.
4. **Explicit uncertainty:** Avoid presenting incomplete annotations as medical certainty.
5. **Reproducible experiments:** Record dataset versions, configurations, and evaluation procedures.
6. **Separation of evidence and assumptions:** Distinguish sourced medical information from algorithmic heuristics.
7. **Responsible data handling:** Use synthetic examples during early development and avoid identifiable patient information.
8. **Measurable progress:** Evaluate improvements using appropriate benchmarks rather than demonstrations alone.

Public availability does not automatically grant permission to redistribute a dataset.

---

## Safety and Intended Use

Medical Context AI is an experimental research and educational project.

It is not a healthcare professional, emergency service, validated diagnostic system, or substitute for qualified medical care.

Its outputs may be incomplete, incorrect, misleading, or inappropriate for a particular medical situation.

The project must not be used to independently diagnose, treat, monitor, or rule out a medical condition, or to determine whether professional medical care is necessary.

A relationship between a disease and a phenotype does not independently establish causation, diagnosis, or clinical likelihood.

Missing annotations must not be interpreted as evidence that a condition is impossible.

The current prototype is not intended for use with real patients or to influence clinical decisions.

Any future clinical application would require separate medical validation, privacy and security assessments, legal and regulatory review, and appropriate professional oversight.

**A disclaimer alone does not make an experimental medical system safe for clinical use.**

---

## Security and Privacy

Do not commit:

- API credentials or access tokens.
- Local `.env` files containing secrets.
- Identifiable patient information.
- Private clinical records.
- Restricted or improperly redistributed datasets.
- Model weights without checking their licenses and distribution permissions.

Credentials should remain in local configuration files excluded from version control.

If a credential is accidentally committed, removing the file from the current repository state is not sufficient. The credential should be revoked or rotated, and repository history reviewed.

---

## Contributions

Contributions to software engineering, ontology integration, data documentation, testing, reproducibility, and research evaluation are welcome.

Areas of interest include:

- Improving disease identity resolution.
- Expanding appropriately licensed disease-phenotype coverage.
- Strengthening automated tests.
- Improving explainability and uncertainty handling.
- Developing reproducible research evaluations.
- Identifying limitations and documenting failure cases.

Medical claims and relationships should be supported by appropriate sources and reviewed by suitably qualified people.

Contributions must not contain identifiable patient data or improperly redistributed medical datasets.

---

## License

Medical Context AI is licensed under the **MIT License**.

See the `LICENSE` file for the full terms.

Third-party datasets, ontologies, APIs, and other resources retain their respective licensing and usage conditions.

---

**Medical Context AI v0.0.2.5 is a functional research prototype, not a promise of medical accuracy.**

Its progress will be measured through transparent methods, reproducible software behavior, carefully documented limitations, and future research evaluation rather than the number of conditions it claims to recognize.