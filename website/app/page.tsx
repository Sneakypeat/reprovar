const variants = [
  { label: "BRCA1 c.68_69del", count: 1, source: "ClinVar", flagged: false },
  { label: "BRCA2 c.5946del", count: 1, source: "ClinVar", flagged: false },
  { label: "TP53 p.Arg273His", count: 1, source: "ClinVar", flagged: false },
  { label: "MLH1 p.Lys618del", count: 1, source: "ClinVar", flagged: true },
  { label: "MUTYH p.Gly396Asp", count: 1, source: "ClinVar", flagged: false },
  { label: "BRAF V600E", count: 111, source: "CIViC", flagged: true },
  { label: "EGFR L858R", count: 48, source: "CIViC", flagged: true },
  { label: "KRAS G12C", count: 18, source: "CIViC", flagged: true },
  { label: "IDH1 R132H", count: 4, source: "CIViC", flagged: true },
  { label: "PIK3CA H1047R", count: 30, source: "CIViC", flagged: true },
];

const workflow = [
  ["01", "Define", "Transcript-aware germline and protein-level somatic identifiers."],
  ["02", "Retrieve", "Official NCBI E-utilities and the CIViC GraphQL API."],
  ["03", "Normalise", "Source identifiers, dates, diseases, therapies and publication links."],
  ["04", "Audit", "Missing, older or context-dependent evidence is surfaced for review."],
  ["05", "Report", "Deterministic tables, a concise report and integrity checks."],
];

const github = "https://github.com/Sneakypeat/reprovar";
const doi = "https://doi.org/10.5281/zenodo.21901951";

function Arrow() {
  return <span aria-hidden="true">↗</span>;
}

export default function Home() {
  return (
    <main>
      <nav className="nav shell" aria-label="Primary navigation">
        <a className="brand" href="#top" aria-label="ReproVar home">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span>ReproVar</span>
        </a>
        <div className="nav-links">
          <a href="#benchmark">Benchmark</a>
          <a href="#method">Method</a>
          <a href="#reproduce">Reproduce</a>
          <a className="nav-cta" href={github} target="_blank" rel="noreferrer">
            GitHub <Arrow />
          </a>
        </div>
      </nav>

      <section className="hero shell" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> Open cancer-variant evidence audit</p>
          <h1>Evidence deserves<br />an audit trail.</h1>
          <p className="hero-deck">
            ReproVar retrieves, normalises and audits public evidence for representative
            germline and somatic cancer variants—without turning database assertions into
            clinical conclusions.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href={github} target="_blank" rel="noreferrer">
              Explore the repository <Arrow />
            </a>
            <a className="button button-secondary" href={doi} target="_blank" rel="noreferrer">
              Cite the release
            </a>
          </div>
          <div className="hero-meta" aria-label="Project metadata">
            <span>v0.1.0</span>
            <span>MIT licensed</span>
            <span>DOI 10.5281/zenodo.21901951</span>
          </div>
        </div>

        <div className="evidence-card" aria-label="Example normalised evidence record">
          <div className="card-topline">
            <span>Evidence record</span>
            <span className="live-dot">public snapshot</span>
          </div>
          <div className="variant-heading">
            <span className="gene">KRAS</span>
            <span className="change">p.Gly12Cys</span>
          </div>
          <dl className="record-grid">
            <div><dt>Source</dt><dd>CIViC EID9431</dd></div>
            <div><dt>Evidence</dt><dd>Level A · rating 5</dd></div>
            <div><dt>Context</dt><dd>Non-small cell lung cancer</dd></div>
            <div><dt>Therapy</dt><dd>Sotorasib</dd></div>
            <div><dt>Publication</dt><dd>PMID 34096690</dd></div>
            <div><dt>Retrieved</dt><dd>12 Aug 2026</dd></div>
          </dl>
          <div className="record-footer">
            <span>PROVENANCE COMPLETE</span>
            <span>SHA-256 VERIFIED</span>
          </div>
        </div>
      </section>

      <section className="numbers" aria-label="Project summary">
        <div className="shell number-grid">
          <div><strong>10</strong><span>benchmark variants</span></div>
          <div><strong>216</strong><span>normalised records</span></div>
          <div><strong>2</strong><span>public knowledgebases</span></div>
          <div><strong>8/8</strong><span>quality checks passing</span></div>
        </div>
      </section>

      <section className="section shell" id="benchmark">
        <div className="section-intro">
          <p className="kicker">The benchmark</p>
          <h2>One question.<br />Two evidence systems.</h2>
          <p>
            Can a compact workflow recover and expose the provenance, review status and
            biological context of public evidence for canonical cancer variants?
          </p>
        </div>

        <div className="coverage-panel">
          <div className="coverage-head">
            <div>
              <span className="panel-label">Evidence coverage</span>
              <h3>Records recovered by variant</h3>
            </div>
            <div className="legend"><span className="teal-dot" /> cleared <span className="coral-dot" /> review flag</div>
          </div>
          <div className="bars">
            {variants.map((variant) => {
              const height = 18 + (Math.log2(variant.count + 1) / Math.log2(112)) * 150;
              return (
                <div className="bar-item" key={variant.label}>
                  <div className="bar-count">{variant.count}</div>
                  <div
                    className={`bar ${variant.flagged ? "flagged" : "cleared"}`}
                    style={{ height: `${height}px` }}
                    title={`${variant.label}: ${variant.count} record${variant.count === 1 ? "" : "s"}`}
                  />
                  <span className="bar-label">{variant.label}</span>
                  <span className="bar-source">{variant.source}</span>
                </div>
              );
            })}
          </div>
          <p className="chart-note">Log-scaled for display. Counts describe source records, not evidence strength.</p>
        </div>
      </section>

      <section className="method section" id="method">
        <div className="shell">
          <div className="section-heading-row">
            <div>
              <p className="kicker">The method</p>
              <h2>From identifier to<br />review-ready evidence.</h2>
            </div>
            <p>
              Every transformation is visible. Raw responses are frozen, normalised rows
              retain their source links, and exceptions are escalated rather than hidden.
            </p>
          </div>
          <ol className="workflow">
            {workflow.map(([number, title, description]) => (
              <li key={number}>
                <span className="step-number">{number}</span>
                <h3>{title}</h3>
                <p>{description}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section shell split" id="reproduce">
        <div className="repro-copy">
          <p className="kicker">Reproducibility</p>
          <h2>Frozen inputs.<br />Deterministic outputs.</h2>
          <p>
            The release can be rebuilt offline with the Python standard library. Snapshot
            hashes, schema tests and report regeneration run on every repository update.
          </p>
          <a className="text-link" href={`${github}/blob/main/docs/METHODS.md`} target="_blank" rel="noreferrer">
            Read the methods <Arrow />
          </a>
        </div>
        <div className="terminal" aria-label="Commands to reproduce ReproVar">
          <div className="terminal-bar"><span /><span /><span /><b>reprovar — zsh</b></div>
          <pre><code><span className="comment"># verify frozen snapshots and outputs</span>{"\n"}$ python -m unittest discover -s tests -v{"\n\n"}<span className="comment"># rebuild the evidence audit offline</span>{"\n"}$ PYTHONPATH=src python -m reprovar.cli analyse{"\n\n"}<span className="success">✓ 8 tests passed · 216 evidence rows written</span></code></pre>
        </div>
      </section>

      <section className="boundary">
        <div className="shell boundary-grid">
          <div>
            <p className="kicker light">Clinical boundary</p>
            <h2>Evidence aggregation<br />is not clinical sign-out.</h2>
          </div>
          <div className="boundary-copy">
            <p>
              ReproVar is a research, training and portfolio project. It does not apply
              ACMG/AMP criteria, assign new somatic tiers, diagnose disease or recommend treatment.
            </p>
            <p>
              Clinical interpretation requires patient context, validated assays, qualified
              personnel and an accredited laboratory process.
            </p>
          </div>
        </div>
      </section>

      <footer className="footer shell">
        <div>
          <a className="brand footer-brand" href="#top"><span className="brand-mark">R</span><span>ReproVar</span></a>
          <p>Built by Syed Sabih Ur Rehman<br />United Arab Emirates University</p>
        </div>
        <div className="footer-links">
          <a href={github} target="_blank" rel="noreferrer">GitHub <Arrow /></a>
          <a href={`${github}/releases/tag/v0.1.0`} target="_blank" rel="noreferrer">Release <Arrow /></a>
          <a href={doi} target="_blank" rel="noreferrer">Zenodo DOI <Arrow /></a>
          <a href="https://orcid.org/0009-0001-0235-1563" target="_blank" rel="noreferrer">ORCID <Arrow /></a>
        </div>
        <div className="footer-note">Open source · MIT licence<br />Public data · No patient information</div>
      </footer>
    </main>
  );
}
