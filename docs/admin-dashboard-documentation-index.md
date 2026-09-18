# MethodAlign IS Admin Dashboard Documentation

This documentation set explains every visible admin dashboard section, every editable parameter, and the research metrics used by the MethodAlign IS comparative engine.

## Client Handover Manual

Start with the [MethodAlign IS Codebase and Application Handover Guide](./codebase-and-application-handover.md) when transferring the application to a new student or non-technical owner. It explains the repository and full source flow with diagrams and annotated excerpts, then links to Windows startup/recovery, administrator, calculation, testing, and maintenance references.

## Recommended Reading Order

1. [Admin Dashboard Guide](./admin-dashboard-guide.md)
   - Explains the dashboard sections: login, navigation, overview, assessments, rules, questionnaire, and users.
   - Best document for a non-technical walkthrough.

2. [Rule And Calculation Reference](./rule-and-calculation-reference.md)
   - Explains how the Agile vs Traditional recommendation is calculated.
   - Covers construct weights, baseline profiles, strictness threshold, outcome dimensions, drivers, risk flags, confidence levels, and hybrid readiness.

3. [Questionnaire And Research Metrics Reference](./questionnaire-and-research-metrics-reference.md)
   - Explains every profile question, Likert question, construct, and research metric.
   - Best document for research panel discussion.

4. [Research Panel Presentation Brief](./research-panel-presentation-brief.md)
   - A presenter-friendly summary with talking points, methodology boundaries, and likely panel questions.

## Core Purpose Of The Admin Dashboard

The admin dashboard supports the research and operational management of MethodAlign IS. It allows authorized users to:

- Review assessment submission counts and methodology trends.
- Inspect individual assessment results.
- Export assessment data for external analysis.
- Tune and version the decision rules.
- Edit and version the questionnaire.
- Manage admin user access.
- View reliability, construct, correlation, t-test, and distribution metrics for research reporting.

## Important Research Boundary

The system is a rule-based decision-support engine. It compares each project profile against two configured research categories: Agile and Traditional. The active weights and reference profiles remain provisional rather than universally validated. Advisory strategy options such as Scrum, Kanban, PRINCE2 Agile, Disciplined Agile, or SAFe are supporting delivery suggestions. They do not replace the core Agile vs Traditional recommendation.
