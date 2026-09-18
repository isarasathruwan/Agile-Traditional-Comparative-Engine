# Admin Dashboard Guide

## 1. Product And Access Context

The admin dashboard belongs to MethodAlign IS. It is used to manage the comparative engine that recommends whether an information systems project is a better fit for Agile or Traditional delivery.

The dashboard has two operating modes:

- Guided mode: shows only the safer day-to-day sections, mainly Overview and Assessments.
- Advanced mode: unlocks Rules, Questionnaire, and Users. These sections can affect future assessment behavior and system access.

## 2. Login Section

The login screen asks for:

| Field | Meaning | Notes |
| --- | --- | --- |
| Email | Admin account email address. | Used to identify the admin user. |
| Password | Admin account password. | Must match the stored password for that user. New users require a password of at least 8 characters. |
| Sign In | Starts an authenticated admin session. | On success, the dashboard stores a bearer token in browser local storage. |

Default seeded development login:

| Field | Value |
| --- | --- |
| Email | `admin@methodalign.local` |
| Password | `admin123` |

This seeded login is useful for development or demonstration, but production deployments should use secure admin credentials.

## 3. Workspace Layout And Controls

After login, the dashboard fills the browser window. On desktop, the section menu stays on the left while only the content workspace scrolls. On tablet and mobile, the same menu opens from the top bar and closes after a section is selected.

The sidebar and mobile menu show:

| Control | Meaning | How to explain it |
| --- | --- | --- |
| Product label | Shows the dashboard belongs to MethodAlign IS. | Confirms the admin user is managing the correct decision-support system. |
| Current section | Is highlighted in the left menu and named in the workspace header. | Helps orient the presenter during a walkthrough. |
| Show Advanced Tools / Advanced Tools On | Switches between guided and advanced mode. | Advanced mode exposes configuration areas that can change future assessments. |
| Download CSV | Exports assessment data. | Used for offline analysis, reporting, or research panel evidence. |
| Sign Out | Ends the current admin session. | Clears the stored admin token from the browser. |

## 4. Navigation Sections

The dashboard contains five main sections:

| Section | Purpose | Available In |
| --- | --- | --- |
| Overview | High-level summary and research metrics. | Guided and Advanced |
| Assessments | Search and inspect submitted assessments. | Guided and Advanced |
| Rules | Configure and version the decision engine. | Advanced only |
| Questionnaire | Configure and version the assessment questions. | Advanced only |
| Users | Create and update admin users. | Advanced only |

Each section also displays a short guidance panel with:

| Item | Meaning |
| --- | --- |
| Tip title | Short purpose of the section. |
| Tip body | What the admin should use that section for. |
| Tip note | Practical warning or recommended action. |

## 5. Overview Section

The Overview section gives a quick snapshot of overall assessment activity.

### 5.1 Total Assessments

| Parameter | Meaning |
| --- | --- |
| Total Assessments | Number of completed assessment submissions stored in the system. |

Presentation explanation:

This is the sample count for the operational dashboard. It shows how many project profiles have gone through the comparative engine.

### 5.2 Agile Recommendations

| Parameter | Meaning |
| --- | --- |
| Agile Recommendations | Number of submissions where the engine recommended Agile as the primary delivery direction. |

Presentation explanation:

This indicates how many assessed projects were closer to the Agile reference profile based on their construct scores and rules.

### 5.3 Traditional Recommendations

| Parameter | Meaning |
| --- | --- |
| Traditional Recommendations | Number of submissions where the engine recommended Traditional as the primary delivery direction. |

Presentation explanation:

This indicates how many assessed projects were closer to the Traditional reference profile, or were forced toward Traditional because strictness exceeded the configured threshold.

### 5.4 Research Metrics In Advanced Mode

When Advanced Tools are enabled, the Overview section can show Research Metrics. These metrics are intended for research validation and panel reporting.

High-level fields:

| Parameter | Meaning |
| --- | --- |
| Sample size | Number of assessment results included in research calculations. |
| Cronbach Alpha | Reliability estimate for each construct's question group. |
| Construct Means | Average construct scores across submissions. |
| Correlations | Pearson correlations between selected construct scores and methodology scores. |
| Independent Sample t-Tests (Welch) | Group comparison statistics between Agile-recommended and Traditional-recommended submissions. |
| Dependent Variable Means | Average scores for the seven outcome dimensions. |
| Confidence Distribution | Counts of high, moderate, and close recommendations. |
| Triggered Risk Flags | Counts of warning signals generated by rules. |
| Hybrid Readiness | Counts of high, moderate, and low hybrid readiness profiles. |
| Delivery Strategies | Counts of advisory delivery strategy labels. |
| Advisory Practices | Counts of recommended supporting practices such as Scrum or Kanban. |

Detailed explanations are in [Questionnaire And Research Metrics Reference](./questionnaire-and-research-metrics-reference.md).

## 6. Assessments Section

The Assessments section lets an admin search, sort, inspect, and export assessment submissions.

### 6.1 Search Box

| Parameter | Meaning |
| --- | --- |
| Search name, company, project, recommendation | Filters the table by matching text in the name, company, project name, or recommendation columns. |

Presentation explanation:

This helps locate a specific respondent or project without reviewing all records manually.

### 6.2 Assessment Table Columns

| Column | Meaning |
| --- | --- |
| Name | Respondent name from the profile section. |
| Company | Organization name from the profile section. |
| Project | Project name submitted by the respondent. |
| Recommendation | Engine output: Agile or Traditional. |
| Details | Opens the detailed assessment view. |

Each sortable column can be clicked to switch between ascending and descending order.

### 6.3 Pagination

| Control | Meaning |
| --- | --- |
| Showing X of Y filtered records | Shows how many rows are visible on the current page and how many match the current search. |
| Prev | Moves to the previous page. |
| Page X / Y | Shows current page and total pages. |
| Next | Moves to the next page. |

The current frontend displays 5 assessment rows per page.

### 6.4 View Details

When an assessment is opened, the dashboard shows:

| Field | Meaning |
| --- | --- |
| Assessment number | Internal submission ID. |
| Recommendation | Final Agile or Traditional result. |
| Agile score | Compatibility score with the Agile reference profile, from 0 to 100. |
| Traditional score | Compatibility score with the Traditional reference profile, from 0 to 100. |
| Rules version | Rule configuration version used when the assessment was calculated. |
| Questionnaire version | Questionnaire version used when the respondent answered. |
| Created date/time | When the assessment was submitted. |

### 6.5 Profile Answers

Profile answers are descriptive project context. They are not Likert construct scores by themselves, but they support reporting and some advisory strategy logic.

Examples:

| Profile key | Meaning |
| --- | --- |
| name | Respondent's name. |
| role | Respondent's role. |
| company | Organization name. |
| industry | Industry category. |
| orgSize | Organization size. |
| projectName | Project name. |
| projectType | Type of project, such as New System or System Integration. |
| duration | Expected project duration. |
| teamSize | Project team size. |
| budget | Budget range. |

### 6.6 Questionnaire Answers

Likert answers are the rated research items. Each answer is scored from 1 to 5 and mapped to one construct:

| Construct | Meaning |
| --- | --- |
| FLEXIBILITY | Adaptability, changing requirements, and stakeholder feedback readiness. |
| PERFORMANCE | Schedule, budget, and delivery performance pressure. |
| STRICTNESS | Security, compliance, governance, and integration control pressure. |

### 6.7 Construct Scores

The detail view shows average scores for:

| Score | Meaning |
| --- | --- |
| FLEXIBILITY | Average of all flexibility-related Likert answers. |
| PERFORMANCE | Average of all performance-related Likert answers. |
| STRICTNESS | Average of all strictness-related Likert answers. |

Each construct score is on a 1 to 5 scale, because it is based on 1 to 5 Likert responses.

### 6.8 Clear Incomplete Activity

Super admins can use **Clear incomplete activity** in the Assessments section to remove abandoned assessment sessions and drafts that never produced a submission.

Before deletion, the dashboard displays the affected session, draft, document, processing-job, evidence-record, and stored-file counts. Confirm the action with **Clear permanently**. The button is disabled only while a worker currently owns an affected document job. Processing statuses left behind by a stopped worker can be cleared safely.

This action does not remove completed submissions, results, linked documents, research metrics, rule versions, questionnaire versions, or admin users. Completed test submissions can be removed separately with their individual Delete controls.

## 7. Download CSV

The CSV export contains:

| Column | Meaning |
| --- | --- |
| submission_id | Internal submission ID. |
| name | Respondent name. |
| company | Organization. |
| project_name | Project name. |
| recommendation | Final Agile or Traditional recommendation. |
| agile_score | Agile compatibility score. |
| traditional_score | Traditional compatibility score. |
| questionnaire_version | Questionnaire version used. |
| created_at | Submission timestamp. |

Presentation explanation:

CSV export allows the researcher to analyze dashboard data outside the application, for example in Excel, SPSS, R, or Python.

## 8. Rules Section

The Rules section is available only in Advanced mode. It controls how future recommendations are calculated.

Important behavior:

- Saving rules creates a new version.
- Activating a version changes the rule set used for future assessments.
- Previous assessment records keep their original rules version for traceability.

Visible rule areas:

| Area | Purpose |
| --- | --- |
| Preview Rules | Tests the current rule draft on sample scenarios before saving. |
| Construct weights | Controls relative importance of FLEXIBILITY, PERFORMANCE, and STRICTNESS. |
| Agile baseline | Defines the ideal Agile reference profile. |
| Traditional baseline | Defines the ideal Traditional reference profile. |
| Strictness Threshold | Forces Traditional when strictness is high enough. |
| Driver Rules | Defines positive factors shown in the decision report. |
| Risk Flag Rules | Defines warnings shown in the decision report. |
| Dependent Variable Rules | Maps constructs to seven research outcome dimensions. |
| Next Step Templates | Defines recommendation-specific action steps. |
| Advanced JSON Editor | Allows full JSON editing of the rules payload. |
| Change note | Records why the new rules version was saved. |
| Save Rules | Saves a new active rules version. |
| Activate vX | Reactivates a previous rules version. |

Detailed calculations are in [Rule And Calculation Reference](./rule-and-calculation-reference.md).

## 9. Questionnaire Section

The Questionnaire section is available only in Advanced mode. It controls the questions shown to assessment users.

Important behavior:

- Saving creates a new questionnaire version.
- Activating a version changes the questions used for future assessments.
- Previous assessment records keep their original questionnaire version.

### 9.1 Questionnaire Title

| Field | Meaning |
| --- | --- |
| Questionnaire title | Human-readable title for the questionnaire version. |

### 9.2 Profile Questions

Profile question fields:

| Field | Meaning |
| --- | --- |
| Question ID | Unique identifier, such as Q1. |
| Kind | `text` for free text or `pill` for selectable options. |
| Profile key | Database/profile field that stores the answer. |
| Prompt | Question text shown to the user. |
| Placeholder | Helper text for text questions. |
| Options | Comma-separated choices for pill questions. |
| Up / Down | Changes question order. |
| Remove | Deletes the question from the draft questionnaire. |

Validation rules:

- Question IDs must be unique across profile and Likert questions.
- Profile keys must be one of the supported keys.
- Pill questions must have at least two options.
- Text questions cannot include options.

### 9.3 Likert Questions

Likert question fields:

| Field | Meaning |
| --- | --- |
| Question ID | Unique identifier, such as Q11. |
| Construct | The research construct the answer contributes to. |
| Prompt | Question text shown to the user. |
| Up / Down | Changes question order. |
| Remove | Deletes the question from the draft questionnaire. |

Validation rules:

- The questionnaire must include Likert questions for FLEXIBILITY, PERFORMANCE, and STRICTNESS.
- Likert answers must be scored from 1 to 5.

### 9.4 Advanced JSON Editor

The Advanced JSON Editor exposes the full questionnaire payload. It should be used carefully because invalid JSON or invalid questionnaire structure can prevent saving.

### 9.5 Save And Activate

| Control | Meaning |
| --- | --- |
| Questionnaire change note | Records why the questionnaire version was changed. |
| Save Questionnaire Version | Creates a new active questionnaire version. |
| Activate Q vX | Makes a previous questionnaire version active again. |

## 10. Users Section

The Users section is available only in Advanced mode and only to users with permission to manage users.

### 10.1 Create User

| Field | Meaning |
| --- | --- |
| Email | Login email for the new admin user. |
| Password | Login password for the new admin user. Must be at least 8 characters. |
| Role | Permission group assigned to the user. |
| Create User | Creates the admin user. |

Available roles:

| Role | Meaning |
| --- | --- |
| analyst | Intended for reviewing analytics and assessments. |
| config_editor | Intended for editing rules and questionnaire configuration. |
| super_admin | Highest access level, including user management. |

### 10.2 Manage Existing Users

| Column | Meaning |
| --- | --- |
| Email | Admin user's login email. |
| Role | Current permission role. |
| Active | Whether the user can log in. |
| Save | Stores role or active-status changes. |

Presentation explanation:

This section supports role-based governance. It separates routine research viewing from configuration editing and full administrative control.
