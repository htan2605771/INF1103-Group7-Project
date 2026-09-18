GITHUB URL: https://github.com/htan2605771/INF1103-Group7-Project
F&B Customer Complaint Triage
1. Problem Statement and Target Users
- What real-world problem does your application aim to solve?
- F&B chains with multiple outlets receive customer complaints daily through various channels (app, email, feedback forms, social media messages), covering everything from minor service issues to serious food safety concerns
- Customer service and outlet managers cannot manually read and prioritize every complaint with equal speed, especially across a large volume
- Complaints about wrong orders or slow service and complaints about hygiene or food safety currently enter the same review queue
- Delayed response to hygiene/food-safety-related complaints carries real reputational and regulatory risk, while low-risk complaints (e.g. missing napkins) don't need the same urgency
- Need for a system that can read incoming complaints and help staff quickly identify which ones require immediate escalation vs routine handling

Who are the intended users of the application?
- Customer service managers (handling complaints across outlets)
- Outlet/branch managers (handling complaints specific to their location)
- Customers submitting complaints

2. User Inputs
What information or data will users provide to the system?
- Name
- Email
- Phone Number
- Outlet/branch name
- Date and time of incident
- Order/transaction reference (if applicable)
- Complaint category selected by customer (e.g. Food Quality, Service, Hygiene, Billing, Other)
- Free-text complaint description
- Whether the customer wants a response/follow-up (Yes/No)

3. Use of AI
- How will AI be utilized within the application?
- Read and interpret the free-text complaint description
- Classify the complaint into a category (hygiene, food quality, service, billing, other) — cross-checked against the customer-selected category
- Assess severity and reputational risk based on the language and content of the complaint
- Extract key details (e.g. specific item mentioned, described symptom/issue, staff behaviour mentioned)
- Convert unstructured complaint text into structured JSON output
- What outputs, insights, or recommendations will the AI generate from the user inputs?
- Complaint category (hygiene, food quality, service, billing, other)
- Key details/issues extracted from the description
- AI severity/risk indicator: Low / Medium / High
- Short reason for the classification
- Flag if the complaint suggests a reputational risk (e.g. mentions intent to post publicly/review platforms)

4. Business Rules
- What business rules, validations, or decision-making logic will be applied to the AI-generated outputs?
- Any complaint containing hygiene/food-safety-related keywords is automatically escalated to at least Medium severity, regardless of the AI's overall tone assessment (rule-based override layer on top of AI classification)
- Multi-condition rule: if outlet has 2+ complaints (of any category) within a defined time window (e.g. 7 days) AND at least one is hygiene-related → auto-flag outlet for management review, not just the individual complaint
- Reject/re-prompt submissions missing outlet ID, category, or description before processing
- Low AI confidence or very short/ambiguous free-text is flagged for manual review rather than auto-classified as "Low" severity
- Complaints flagged as reputational risk (e.g. customer states intent to leave public review) are routed to customer service managers for priority response, separate from the severity-based routing
- All hygiene-flagged complaints are logged persistently (CSV/JSON) to support trend tracking across outlets over time, even after resolution
