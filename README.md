# Automated Examination Schedule Planner

## 1. Project Overview

Build a full-stack web application called **Automated Examination Schedule Planner** that automatically generates examination timetables for college semesters.

The application should allow administrators to configure a semester, add subjects, configure examination durations, set examination date windows, specify holidays, configure laboratory batches, and generate a conflict-free examination schedule.

The system must be modular, maintainable, scalable, user-friendly, and built using modern full-stack development practices.

This is a **rule-based scheduling application**. It must not depend on artificial intelligence, AI APIs, LLMs, chatbots, or external AI services for any functionality.

The scheduling must be accomplished using traditional programming logic, algorithms, date calculations, validation and constraint checking.

---

## 2. Technology Stack

### Frontend
- React
- Vite
- JavaScript
- CSS
- Responsive and modern UI

### Backend
- Python
- FastAPI
- REST API architecture

### Database
- SQLite for local development
- MySQL compatibility for future deployment

### Scheduling Engine
- Python
- Modular scheduling algorithms
- Constraint-based validation
- Deterministic rule-based scheduling

### Export
- PDF timetable export

---

## 3. Main Application Workflow

The application should follow this workflow:

1. Create a semester examination plan.
2. Select the semester.
3. Configure the academic year.
4. Configure semester start and end dates.
5. Add subjects.
6. Configure subject types and examination requirements.
7. Configure examination date windows.
8. Configure holidays and non-working days.
9. Configure laboratory batches.
10. Generate the examination timetable.
11. Validate the timetable.
12. Display the generated timetable.
13. Allow manual editing.
14. Allow regeneration.
15. Export the final timetable as a PDF.

The application must save plans so that users can reopen and modify them later.

---

## 4. Semester Configuration

The application must support semesters:

- Semester 3
- Semester 4
- Semester 5
- Semester 6
- Semester 7
- Semester 8

Each examination plan must contain:

- Semester number
- Academic year
- Semester start date
- Semester end date
- Examination plan title
- Optional description

The application must calculate scheduling periods relative to the semester start date.

Do not assume that semesters start on the first day of a month.

The system must handle semester start and end dates that fall in the middle of a month.

---

## 5. Subject Management

Users must be able to add, edit and delete subjects.

Each subject must contain:

- Subject code
- Subject name
- Subject category
- Number of IATs
- IAT duration
- SEE duration
- Laboratory internal duration
- Laboratory external duration
- Is mathematics-related
- Number of laboratory batches

### Subject Categories

#### Theory

A theory subject requires:

- Internal Assessment Tests (IATs)
- Semester End Examination (SEE)

It does not require laboratory examinations.

#### Practical

A practical subject requires:

- Laboratory Internal examinations
- Laboratory External examinations

It does not require a SEE.

#### Both

A subject categorized as Both requires:

- Internal Assessment Tests (IATs)
- SEE
- Laboratory Internal examinations
- Laboratory External examinations

---

## 6. Internal Assessment Test (IAT) Scheduling

The application must support configurable IAT scheduling.

### Default IAT Periods

Schedule IATs according to semester-relative periods:

- IAT 1: Second month of the semester
- IAT 2: Third month of the semester
- IAT 3: Fourth month of the semester

The user must be able to modify the scheduling date window for each IAT.

### Default IAT Slots

Morning:

- 09:30 AM – 11:00 AM

Afternoon:

- 02:30 PM – 04:00 PM

These slots should be configurable.

### IAT Scheduling Rules

1. Mathematics-related subjects must be scheduled first.
2. Remaining subjects must be sorted in ascending order by subject code.
3. The same subject ordering must be followed for IAT 1, IAT 2 and IAT 3.
4. Each subject must be scheduled only for the IATs it requires.
5. The scheduling algorithm must respect the configured date windows.
6. Holidays and weekends must be excluded.
7. A subject must not be scheduled simultaneously with another assessment that violates the configured conflict rules.
8. The system must detect scheduling conflicts and explain them.

---

## 7. Laboratory Internal Scheduling

Laboratory Internal examinations must be scheduled within a user-configurable date window.

### Rules

1. Each laboratory subject can have multiple batches.
2. All batches belonging to the same subject should normally be scheduled on the same day.
3. Different batches must be assigned separate time slots.
4. Batch scheduling must respect configurable duration.
5. Laboratory internal examinations must not fall on weekends or holidays.
6. Laboratory internal scheduling must respect other configured scheduling constraints.
7. The number of batches and batch durations must be configurable.

The system should allow the user to configure how many batches can be scheduled per day.

If scheduling becomes impossible, the system must report the problem rather than silently violating constraints.

---

## 8. Laboratory External Scheduling

Laboratory External examinations must be scheduled within a configurable date window.

### Rules

1. Only subjects categorized as Practical are eligible for laboratory external scheduling.
2. Subjects categorized as Both must not be included in laboratory external scheduling unless the administrator explicitly changes this rule.
3. Laboratory External examinations must be scheduled after IAT 3.
4. The date window must be configurable.
5. Maximum two batches may be scheduled per day by default.
6. Each laboratory external examination must have a configurable duration.
7. Laboratory External examinations must not fall on weekends or holidays.
8. The system must detect conflicts.
9. The system must report unscheduled examinations and the reasons.

---

## 9. Semester End Examination (SEE) Scheduling

SEE examinations must be scheduled toward the end of the semester within a configurable date window.

### Rules

1. Theory subjects must receive SEE examinations.
2. Subjects categorized as Both must receive SEE examinations.
3. Pure Practical subjects must not receive SEE examinations.
4. One SEE examination must be scheduled per day by default.
5. There must be at least one full working day gap between SEE examinations.
6. Holidays and weekends must be excluded.
7. SEE durations must be configurable.
8. The SEE date window must be configurable.
9. The algorithm must detect conflicts and report unscheduled examinations.

---

## 10. Holidays and Non-Working Days

Users must be able to add holidays and other non-working days to a semester plan.

Each holiday should have:

- Date
- Holiday name
- Optional description

The scheduling engine must exclude:

- Saturdays
- Sundays
- Configured holidays
- Configured non-working days

This exclusion must apply to:

- IATs
- Laboratory Internals
- Laboratory Externals
- SEEs

Allow administrators to configure the weekend policy in the future.

---

## 11. Scheduling Engine

The scheduling engine must be modular.

Do not implement all scheduling logic in a single massive function.

Separate scheduling logic into modules.

Suggested modules:

- `common.py` – Shared scheduling utilities
- `iat.py` – IAT scheduling
- `lab_internal.py` – Laboratory internal scheduling
- `lab_external.py` – Laboratory external scheduling
- `see.py` – SEE scheduling
- `engine.py` – Main scheduling orchestration

### Scheduling Engine Responsibilities

- Generate valid examination dates.
- Exclude holidays and weekends.
- Respect configured date windows.
- Respect examination durations.
- Respect assessment ordering rules.
- Respect subject categories.
- Respect batch constraints.
- Detect conflicts.
- Report scheduling failures.
- Generate a structured timetable.
- Support regeneration.

### Conflict Detection

The application must detect:

- Duplicate examinations for the same subject and assessment.
- Invalid examination dates.
- Examinations scheduled outside configured windows.
- Weekend scheduling.
- Holiday scheduling.
- Invalid assessment types for subjects.
- Batch conflicts.
- Slot conflicts.
- Violations of SEE spacing rules.
- Violations of IAT ordering rules.

The scheduling engine must never silently ignore a failed constraint.

The engine must clearly differentiate between hard constraints and configurable scheduling preferences.

Hard constraints must never be violated during automatic generation.

If a valid schedule cannot be generated, the system must provide an explanation instead of silently generating an invalid timetable.

---

## 12. Frontend Requirements

Build a clean, professional and intuitive dashboard.

The frontend should be responsive and usable on desktop and tablet.

### Main Pages or Sections

#### Dashboard

Display:

- Existing examination plans
- Semester
- Academic year
- Plan status
- Create new plan button

#### Semester Configuration

Allow users to:

- Select semester
- Enter academic year
- Enter semester start date
- Enter semester end date
- Enter plan title

#### Subject Management

Allow users to:

- Add subjects
- Edit subjects
- Delete subjects
- View subjects in a table
- Sort subjects
- Validate subject data

#### Scheduling Configuration

Allow users to configure:

- IAT date windows
- IAT slots
- Laboratory internal window
- Laboratory external window
- SEE window
- Batch limits
- Examination durations
- Weekend policy

#### Holiday Management

Allow users to:

- Add holidays
- Remove holidays
- View holidays

#### Timetable Generation

Allow users to:

- Generate timetable
- View generated timetable
- View scheduling warnings
- View unscheduled examinations
- Regenerate timetable

#### Timetable Viewer

Display the timetable in a structured table.

The table should include:

- Date
- Day
- Examination type
- Subject code
- Subject name
- Batch
- Start time
- End time

Allow filtering by:

- Examination type
- Date
- Subject
- Semester

#### Manual Editing

Users must be able to manually edit generated timetable entries.

When an entry is edited:

- Validate the edited entry.
- Detect potential conflicts.
- Warn the user about constraint violations.
- Do not silently accept invalid schedules.

#### PDF Export

Allow users to export the final timetable to PDF.

The PDF should:

- Have a professional layout.
- Include semester and academic year.
- Include examination dates.
- Include examination types.
- Include subject codes and names.
- Include batch details when applicable.
- Be readable when printed.

---

## 13. Backend Requirements

Create a FastAPI backend with REST APIs.

### Expected API Operations

#### Examination Plans

- Create plan
- Get all plans
- Get plan by ID
- Update plan
- Delete plan

#### Subjects

- Create subject
- Get subjects for a plan
- Update subject
- Delete subject

#### Holidays

- Add holiday
- Get holidays
- Delete holiday

#### Scheduling

- Generate schedule
- Get generated schedule
- Validate schedule
- Regenerate schedule

#### Export

- Export timetable as PDF

Use:

- Appropriate HTTP methods
- HTTP status codes
- Validation
- Error handling
- Clear API response structures

---

## 14. Database Design

Design a normalized database.

Suggested entities:

### ExaminationPlan

- ID
- Semester
- Academic year
- Start date
- End date
- Title
- Description
- Created timestamp
- Updated timestamp

### Subject

- ID
- Examination plan ID
- Subject code
- Subject name
- Category
- IAT count
- IAT duration
- SEE duration
- Laboratory internal duration
- Laboratory external duration
- Mathematics-related flag
- Number of batches

### Holiday

- ID
- Examination plan ID
- Date
- Name
- Description

### ScheduleConfiguration

- ID
- Examination plan ID
- IAT date windows
- IAT slots
- Laboratory internal date window
- Laboratory external date window
- SEE date window
- Batch configuration

### ScheduleEntry

- ID
- Examination plan ID
- Subject ID
- Assessment type
- Date
- Start time
- End time
- Batch number
- Status

The database schema can be refined during development, but it must support the required features.

---

## 15. Architecture and Code Quality

Follow these practices:

- Separate frontend and backend.
- Use reusable React components.
- Keep API communication separate from UI components.
- Use modular backend architecture.
- Keep scheduling logic independent of API routes.
- Use validation schemas.
- Use proper database models.
- Avoid hardcoding semester dates.
- Avoid hardcoding subject lists.
- Avoid hardcoding holidays.
- Avoid hardcoding scheduling windows.
- Make configurable rules configurable.
- Use meaningful variable and function names.
- Write comments for complex algorithms.
- Handle errors gracefully.
- Avoid unnecessary duplication.
- Keep code maintainable.

---

## 16. Testing

Write automated tests for the scheduling engine.

Test:

- Weekend exclusion
- Holiday exclusion
- IAT scheduling order
- Mathematics-related subjects first
- Subject code ordering
- IAT date windows
- Laboratory internal batches
- Laboratory external eligibility
- Laboratory external scheduling after IAT 3
- SEE subject eligibility
- SEE gap rules
- Conflict detection
- Unscheduled examinations
- Empty subject lists
- Invalid date windows
- Edge cases

Use pytest for backend tests.

---

## 17. Deployment

The application should be designed so it can eventually be deployed.

Potential deployment architecture:

- Frontend: Vercel or Netlify
- Backend: Render, Railway or another Python hosting provider
- Database: MySQL or hosted relational database

Local development must remain straightforward.

Document deployment steps when deployment is implemented.

---

## 18. Project Structure

Maintain a structure similar to:

```text
Exam-Schedule-Planner/
│
├── README.md
├── ROADMAP.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── SETUP.md
├── API.md
├── .gitignore
│
├── frontend/
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── components/
│       ├── pages/
│       └── styles.css
│
└── backend/
    ├── requirements.txt
    ├── tests/
    └── app/
        ├── main.py
        ├── database.py
        ├── models.py
        ├── schemas.py
        └── scheduler/
            ├── common.py
            ├── iat.py
            ├── lab_internal.py
            ├── lab_external.py
            ├── see.py
            └── engine.py
```

The structure can evolve as the application grows, but preserve modularity and separation of concerns.

---

## 19. Development Roadmap

Build the application in the following phases.

### Phase 1 – Project Foundation

- Initialize frontend.
- Initialize backend.
- Configure development environment.
- Configure database.
- Connect frontend and backend.

### Phase 2 – Semester Plan Management

- Create examination plans.
- Edit examination plans.
- View plans.
- Delete plans.

### Phase 3 – Subject Management

- CRUD operations for subjects.
- Subject validation.
- Subject category handling.

### Phase 4 – Configuration

- IAT windows.
- Lab internal window.
- Lab external window.
- SEE window.
- Examination slots.
- Holiday configuration.

### Phase 5 – Scheduling Engine

- Shared date utilities.
- IAT scheduler.
- Lab internal scheduler.
- Lab external scheduler.
- SEE scheduler.
- Main scheduler.
- Conflict detection.

### Phase 6 – Schedule Generation

- Integrate scheduler with API.
- Generate timetable.
- Store schedule.
- Display schedule.
- Report scheduling failures.

### Phase 7 – Editing and Validation

- Manual editing.
- Conflict warnings.
- Schedule validation.
- Regeneration.

### Phase 8 – PDF Export

- Generate timetable PDF.
- Implement print-friendly formatting.

### Phase 9 – Testing

- Scheduler tests.
- API tests.
- Frontend testing.
- Integration testing.

### Phase 10 – Deployment

- Prepare deployment configuration.
- Deploy frontend.
- Deploy backend.
- Configure database.
- Document deployment.

---

## 20. AI Integration Restrictions

This application must be developed and operate without artificial intelligence integration.

### Explicitly Prohibited as Application Features

- AI APIs
- LLM integrations
- OpenAI API integrations
- AI-based scheduling
- AI chatbot
- AI assistant within the application
- AI-generated scheduling decisions
- AI-dependent validation
- AI-dependent timetable generation

The application must function independently without any AI service, API key, external AI provider, or AI-related dependency.

The scheduling process must be implemented entirely using conventional programming techniques, algorithms, data structures, rules, constraints and database operations.

AI coding tools may be used externally to develop the project, but AI must not be part of the final application's runtime architecture.

---

## 21. Existing Development Progress

### Work Already Completed

The project has already been initialized and development has begun.

The following work has already been completed, up to Step 6 of the initial development setup:

- Initial project setup has been completed.
- The project development environment has been established in VS Code.
- The frontend project has been initialized using React and Vite.
- The initial frontend structure has been set up.
- The backend project has been initialized using Python and FastAPI.
- The initial backend structure has been set up.
- The initial setup and development work has been completed through Step 6 of the original setup process.

### Current Development Status

| Task | Status |
|---|---|
| Initial project setup | Completed |
| VS Code development environment | Completed |
| React + Vite initialization | Completed |
| Initial frontend structure | Completed |
| FastAPI initialization | Completed |
| Initial backend structure | Completed |
| Initial setup through Step 6 | Completed |
| Remaining application features | Pending |

The completion status above refers to the initial setup, not the completion of the examination scheduling application itself.

The AI coding agent must inspect the existing files and verify the actual implementation before assuming that any specific functionality has been completed.

### Instructions for Continuing Development

**Do not restart the project from scratch.**

Before writing, deleting, replacing or reorganizing code:

1. Inspect the existing project files and folders.
2. Identify which features and setup steps are already working.
3. Preserve the existing working frontend and backend setup.
4. Reuse the existing files, configurations and dependencies wherever possible.
5. Do not recreate the React/Vite or FastAPI project if it already exists.
6. Do not overwrite working code without a valid reason.
7. Continue development from the current state of the project.
8. If a previously completed step is incomplete or broken, explain the issue before modifying it.

### Next Development Objective

Continue from the existing project setup and begin implementing the remaining features in the roadmap, starting with the appropriate next phase.

Do not treat the project as a fresh installation.

---

## 22. Instructions for AI Coding Agents

You are the lead full-stack developer for this project.

Treat this README as the primary project specification.

### Your Responsibilities

1. Read the entire README before modifying the project.
2. Inspect the existing project structure before creating or modifying files.
3. Do not unnecessarily overwrite existing working code.
4. Follow the roadmap in sequence unless dependencies justify changing the order.
5. Implement actual working code, not pseudocode or placeholders.
6. Do not skip backend functionality while implementing frontend functionality.
7. Do not create buttons that do nothing.
8. Do not use mock data as a substitute for implemented backend features.
9. Do not silently ignore scheduling constraints.
10. Write tests for important scheduling rules.
11. Keep the project runnable after each development phase.
12. Explain which files you created or modified.
13. Explain how to run and test each implemented phase.
14. If a feature is incomplete, clearly identify it.
15. Ask for clarification only when a requirement genuinely cannot be reasonably inferred.

### Working Mode

Work like an experienced software engineer.

- Plan before implementation.
- Implement incrementally.
- Verify your code.
- Debug errors.
- Preserve working functionality.
- Use clean architecture.
- Avoid unnecessary complexity.
- Do not stop after generating a plan if actual implementation is requested.

If working in an AI coding environment capable of editing files, use that capability directly to implement the project.

If the project already contains code, continue from the existing implementation instead of rebuilding everything from scratch.

The ultimate goal is a complete, working Automated Examination Schedule Planner, not merely a prototype UI.
