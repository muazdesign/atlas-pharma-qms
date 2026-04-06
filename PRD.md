Product Requirements Document (PRD): Atlas Pharma QMS
1. Project Vision
The Atlas Pharma QMS is a secure, closed-loop Electronic Quality Management System (eQMS). Built using Python and Streamlit, it automates the "Feedback-to-Resolution" loop for Paracetamol (Tablet & Syrup) production. It features a public-facing review gateway, an AI-driven triage system, and an internal portal for Quality Managers (Maimouna and Büşra) to track specs, manage labs, and log CAPA (Corrective and Preventive Action) resolutions.
2. Tech Stack & Environment
•	Development Tool: Anti Gravity Agent (Vibe Coding).
•	Core Framework: Python / Streamlit.
•	Database: SQLite (Local, lightweight relational database).
•	AI Integration: OpenAI API (for natural language processing and review triage).
•	Data Vis & Flow: Pandas (data manipulation), Plotly (dashboards), and a Streamlit-compatible flowchart/graphing library for the interactive process map.
3. Database Architecture (SQLite)
The system requires a persistent database to function as a true QMS. Anti Gravity Agent should initialize the following tables:
•	users: id, username, password_hash, role (e.g., Admin, Quality Manager, Guest).
•	reviews: id, batch_number, product_type, review_text, ai_category (Major/Minor/Critical), status (Open/Claimed/Resolved).
•	specs_master: Maimouna’s physical and functional product definitions.
•	partners_directory: Büşra’s testing labs and regulatory standards (TSE, TÜBİTAK, TİTCK).
•	capa_logs: id, review_id, root_cause, preventive_action, manager_assigned, timestamp.
4. User Roles & Authentication
•	Public Access: No login required. Can only access the Feedback Gateway.
•	Internal Access (Secured): Requires username/password.
o	Executives: View-only access to the Dashboard.
o	Quality Managers (Maimouna & Büşra): Read/Write access to Triage, Specs, Partners, and CAPA Tracker.
5. Site Architecture (The Pages)
Page 0: The Gatekeeper (Auth)
•	Function: A clean login screen.
•	Logic: Routes authenticated users to the internal QMS and unauthenticated users to an "Access Denied" state (unless they are on the public form URL).
Page 1: Public Feedback Gateway
•	Function: Data collection form.
•	Fields: Product Type (Dropdown), Batch Number (Text), Issue Description (Text Area).
•	Logic: Upon submission, the AI categorizes the complaint and saves it to the reviews table.
Page 2: Executive Dashboard
•	Function: High-level analytics and oversight.
•	Visuals:
o	AI Categorization Pie Chart (Major/Minor/Critical).
o	Monthly trend line of reported issues.
o	Open vs. Resolved ticket counters.
Page 3: AI Triage Inbox
•	Function: The active workspace for Quality Managers.
•	Visuals: A data table of incoming reviews. Rows tagged as "Critical" are highlighted in red.
•	Logic: Managers can click a "Claim" button on a row to assign the ticket to themselves, updating the database status.
Page 4: Product Specs & Lab Partners
•	Function: The "Source of Truth" reference hub.
•	Visuals:
o	Specs Tab: Searchable table of Maimouna's Paracetamol standards.
o	Partners Tab: Directory of Büşra's testing institutions and ISO/ISTA standards.
Page 5: CAPA Tracker
•	Function: Logging the resolution and preventive measures.
•	Logic: Managers select a claimed ticket, input the Root Cause, define the Action Taken, and hit "Resolve." This updates the ticket status and logs the event in the capa_logs table.
Page 6: Interactive Flowchart
•	Function: A dynamic visual representation of the quality workflow.
•	Logic (State Management): The chart listens to the database. If a ticket is in "Triage," step 1 lights up. When it moves to "CAPA," step 2 lights up. When "Resolved," step 3 turns green.
6. UI/UX & Branding
•	Color Palette: Atlas Blue (#0056b3) and Clean White (#ffffff).
•	Vibe: Corporate, clinical, organized, and data-driven.
•	Layout: Standard enterprise dashboard layout (Sidebar navigation for internal pages, main content area for data and forms).
7. Recommended Build Sequence for Anti Gravity Agent
1.	Prompt 1: "Initialize a Streamlit app with an SQLite database containing a users and reviews table. Build a basic login page."
2.	Prompt 2: "Build the Public Feedback Gateway that writes to the reviews table."
3.	Prompt 3: "Integrate AI to automatically categorize new reviews as Major, Minor, or Critical."
4.	Prompt 4: "Build the Triage Inbox to display the reviews and add a 'Claim' button."
5.	Prompt 5: "Build the CAPA tracker, Specs/Partners tables, and the interactive Flowchart that updates based on the review status."

