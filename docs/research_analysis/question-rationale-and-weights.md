# Question Selection, Evidence, and Weight Justification

Q1–Q10 are profile/context questions and have **zero weight** in the Agile-versus-Traditional compatibility calculation. Q11–Q22 are scored. The original survey did not measure every Version 2 item exactly, so evidence strength is stated explicitly.

| ID | Construct | Why selected | Survey support | Qualitative support | Evidence status | Effective item influence |
| --- | --- | --- | --- | --- | --- | ---: |
| Q11 | FLEXIBILITY | Requirement volatility is the strongest closed-question separator and directly determines how useful iterative reprioritization may be. | Requirements Change (eta-squared=0.682) | Requirement uncertainty/scope: 27/69 challenges and 21/71 important-factor answers. | Direct quantitative + qualitative | 11.41% |
| Q12 | FLEXIBILITY | Solution uncertainty captures discovery work that simple requirement-change frequency does not fully describe. | Requirements Change (eta-squared=0.682); Flexibility Need (eta-squared=0.651) | Requirement uncertainty/scope: 27/69 challenges and 21/71 important-factor answers. | Indirect quantitative + qualitative | 11.41% |
| Q13 | FLEXIBILITY | Iterative delivery requires available stakeholders with enough authority to provide timely feedback and priority decisions. | Stakeholder Involvement (eta-squared=0.337) | Stakeholders/communication: 19/69 challenges and 17/71 important-factor answers. | Related quantitative + qualitative | 11.41% |
| Q14 | FLEXIBILITY | The open responses identify team maturity and culture as the most frequent self-reported selection factor. | No exact closed survey factor | Team capability/culture: 16/69 challenges and 22/71 important-factor answers. | Qualitative/proxy | 11.41% |
| Q15 | PERFORMANCE | Externally fixed dates reduce delivery-plan discretion and increase the importance of predictive control. | Deadline Pressure (eta-squared=0.222) | Time/budget/planning: 11/69 challenges and 5/71 important-factor answers. | Related quantitative + qualitative | 7.12% |
| Q16 | PERFORMANCE | A fixed funding ceiling constrains scope, schedule, and delivery trade-offs. | Budget Pressure (eta-squared=0.299) | Time/budget/planning: 11/69 challenges and 5/71 important-factor answers. | Related quantitative + qualitative | 7.12% |
| Q17 | PERFORMANCE | Approval gates determine whether the team can make iterative trade-offs without procurement, board, or contractual escalation. | No exact closed survey factor | Governance/compliance/security: 17/69 challenges and 16/71 important-factor answers. | Qualitative/proxy | 7.12% |
| Q18 | STRICTNESS | Mandatory obligations create evidence, approval, and traceability requirements that must shape delivery governance. | Security Requirements (eta-squared=0.416); Documentation Need (eta-squared=0.542) | Governance/compliance/security: 17/69 challenges and 16/71 important-factor answers. | Indirect quantitative + qualitative | 6.60% |
| Q19 | STRICTNESS | Failure consequence distinguishes routine delivery risk from safety, privacy, financial, or legally significant exposure. | Project Risk (eta-squared=0.399); Security Requirements (eta-squared=0.416) | Quality/risk/safety: 8/69 challenges and 10/71 important-factor answers. | Related quantitative + qualitative | 6.60% |
| Q20 | STRICTNESS | Formal documentation and traceability were among the strongest Traditional-oriented separators in the survey. | Documentation Need (eta-squared=0.542) | Documentation/control: 15/69 challenges and 4/71 important-factor answers. | Direct quantitative + qualitative | 6.60% |
| Q21 | STRICTNESS | External technical dependencies constrain sequencing, release timing, testing, and change autonomy. | Integration Complexity (eta-squared=0.253) | Technical delivery context: 9/69 challenges and 9/71 important-factor answers. | Related quantitative + qualitative | 6.60% |
| Q22 | STRICTNESS | Larger and cross-organizational projects require more explicit coordination and dependency management. | Project Size (eta-squared=0.415) | Coordination appeared across stakeholder, technical-context, and governance responses. | Proxy quantitative + qualitative | 6.60% |

## How the weights were obtained

For each construct, eta-squared values from its mapped Google Form factors were averaged. The three averages were then normalized to sum to 3. This produces weights of 1.37 for adaptation/readiness, 0.64 for delivery constraints, and 0.99 for assurance/dependencies.

Questions are not assigned 12 separate fitted coefficients. They contribute equally to their construct average, so their nominal overall influence equals the construct share divided by the number of questions in that construct.

## Interpretation boundary

The weights describe how strongly factors separated respondents by the methodology they reported using. They do not prove which methodology should have been used. Several items use indirect or qualitative evidence and still require expert content review, cognitive interviews, and independent expert-labelled project cases.

## Item-level validation needs

- **Q11**: Historical association does not prove that changing requirements caused the methodology choice.
- **Q12**: Acceptance-criteria uncertainty was not a separate closed survey item and needs expert/cognitive validation.
- **Q13**: Past involvement is not identical to future availability or decision authority.
- **Q14**: Team short-cycle capability was not measured by a closed survey item.
- **Q15**: Deadline importance is not identical to an immovable external deadline.
- **Q16**: Budget importance is only a proxy for contractual funding rigidity.
- **Q17**: Change-approval authority was not measured as a closed survey variable.
- **Q18**: Regulatory and audit obligations were not isolated from security/documentation in the closed survey.
- **Q19**: The original risk and security ratings did not use consequence-based anchors.
- **Q20**: Documentation need may partly reflect the sample's industry composition.
- **Q21**: Integration complexity can exist without an external dependency.
- **Q22**: Team size is a proxy; it does not directly measure coupling or sequencing.
