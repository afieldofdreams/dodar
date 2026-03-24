export default function AboutPage() {
  return (
    <div className="container">
      <section className="about-hero">
        <h1>About DODAR</h1>
        <p style={{ fontSize: "1.125rem", color: "var(--text-light)", maxWidth: 640 }}>
          A structured reasoning framework born in the cockpit, built for AI agents.
        </p>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>The origin story</h2>
        <p>
          DODAR was created by Adam Field — a former commercial pilot turned AI
          product leader. The framework draws directly from Crew Resource
          Management (CRM), the discipline that transformed aviation safety by
          giving flight crews structured decision-making tools for high-pressure,
          time-critical situations.
        </p>
        <p>
          In the cockpit, premature action under uncertainty kills. CRM training
          teaches pilots to hold diagnosis open, enumerate options, commit with
          transparency, act concretely, and review continuously. These principles
          have been refined over decades of incident investigation and are now
          standard in every commercial airline.
        </p>
        <p>
          The insight behind DODAR for AI is that language models fail at complex
          decision tasks in the same ways humans fail under pressure: through
          premature closure, option narrowing, and skipping critical reasoning
          steps. The framework compensates by externalising the decision process
          into an explicit scaffold.
        </p>

        <div className="finding-highlight">
          <p>
            "A new first officer has the technical knowledge to fly the aircraft but
            may lack the metacognitive discipline to manage a non-normal situation
            under pressure. CRM provides the external scaffold. Experienced
            captains internalise this discipline over time and no longer need the
            explicit framework. The same pattern appears in LLMs: frontier models
            have internalised the reasoning discipline that small models need
            externally provided."
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Adam Field</h2>
        <p>
          Technical founder and AI product leader with 10+ years building and
          deploying machine learning systems in highly regulated environments.
        </p>

        <div className="timeline">
          <div className="timeline-item">
            <div className="timeline-year">2002</div>
            <h3>Commercial Pilot Licence — Oxford Aviation (91%)</h3>
            <p>Flew for Ryanair. Experienced CRM and structured decision-making in safety-critical operations first-hand.</p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2014</div>
            <h3>BSc Software Engineering — Middlesex University (First Class)</h3>
            <p>Transitioned from aviation to technology.</p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2013 — 2017</div>
            <h3>Technical Project Manager — Potato (WPP)</h3>
            <p>Delivered large-scale technical builds including a $2M redesign of the Android Developers site.</p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2017 — 2018</div>
            <h3>AI Product Manager — Babylon Health</h3>
            <p>
              Led product development for Babylon's AI clinical triage chatbot.
              Launched the UK's first BSI-audited AI clinical chatbot across 12 countries
              under ISO 13485, MDR and DCB 0129 compliance.
            </p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2018 — 2020</div>
            <h3>Product Manager — Forward Partners</h3>
            <p>
              Built Forward Advances, an automated revenue-based finance product.
              Integrated Open Banking data to automate underwriting. Reduced credit
              decision time from two weeks to two days.
            </p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2020 — 2022</div>
            <h3>Lead Product Manager — Health Navigator</h3>
            <p>
              AI risk stratification and clinical coaching platform for NHS trusts.
              Reduced unplanned hospital readmissions by 35% through targeted AI intervention.
            </p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2022 — present</div>
            <h3>Head of Product — SideLight AI</h3>
            <p>
              Building medical and medical-legal AI systems. Led zero-to-one development
              of AI prototypes for clinical documentation, evidence review, and workflow
              automation. Delivered live pilots with Tier 1 and Tier 2 law firms.
            </p>
          </div>
          <div className="timeline-item">
            <div className="timeline-year">2026</div>
            <h3>DODAR Framework — Crox</h3>
            <p>
              Published the DODAR validation benchmark and whitepaper. Open-source
              framework and Python SDK for structured AI agent reasoning.
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Why this matters</h2>
        <p>
          The default approach to AI-assisted decision-making is to use the most
          capable model available and rely on its native reasoning. But frontier
          API pricing is dramatically higher than small model equivalents. A single
          Opus 4.6 zero-shot query costs $0.14 on average, compared to $0.0003
          for GPT-4.1 Nano.
        </p>
        <p>
          DODAR demonstrates that you don't always need a bigger model — you need
          a better structure. The framework enables small, cheap models to produce
          reasoning quality that matches or exceeds frontier models at a fraction
          of the cost.
        </p>
        <p>
          For high-volume production workloads — clinical decision support,
          legal document review, financial risk assessment — this cost-efficiency
          multiplier is the difference between viable and prohibitively expensive
          AI deployment.
        </p>
      </section>

      <section className="section" style={{ paddingBottom: "4rem" }}>
        <h2>Contact</h2>
        <p>
          <a href="mailto:adam@crox.io">adam@crox.io</a>
        </p>
        <div className="btn-group" style={{ justifyContent: "flex-start", marginTop: "1rem" }}>
          <a href="https://www.linkedin.com/in/afieldio" target="_blank" rel="noopener noreferrer" className="btn btn-secondary">LinkedIn</a>
          <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener noreferrer" className="btn btn-secondary">GitHub</a>
          <a href="https://crox.io" target="_blank" rel="noopener noreferrer" className="btn btn-secondary">crox.io</a>
        </div>
      </section>
    </div>
  );
}
