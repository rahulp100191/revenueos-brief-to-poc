# What We Left Out

To complete the main event-to-decision workflow within one day, I did not include:

* Real integrations with CRM, call-recording, enrichment, knowledge storage, or notification systems. Instead, we used mock data that follows realistic event formats.
* Slack, Teams, or email notifications. The prototype creates an internal alert with an owner and relevant context.
* Login, permissions, multi-tenant support, and production deployment. The demo uses one reviewer in one environment.
* Extra workflows, delay reasons, regional rules, holiday calendars, PDF export, and an AI evaluation framework. These are useful future improvements but outside the main Sales-to-PreSales workflow.
* A production database and reliable event storage. JSON files were faster for the demo, but they are not safe when many users write data at the same time.
* Background job processing and saved LangGraph workflow states. The prototype runs AI calls immediately and keeps workflow state in memory.

The system calculates SLA status using the timestamps in each brief. When an SLA is missed, it automatically creates an alert that includes an owner and relevant business context.

In this prototype, the SLA check happens when someone opens the brief. In production, a background service would continuously check SLAs and create alerts automatically.

# What Would Break at 10x Usage

The following areas would likely fail first:

* AI calls would become slow and could time out.
* Multiple users could update the same JSON files and cause data conflicts.
* In-memory workflow data could be lost when the application restarts.
* Chroma startup and document embedding would become slower.
* A single application process would struggle with the increased workload.
* Alerts would remain inside the application instead of reaching users through Slack, Teams, or email.

For production, we would add:

* A proper database or event store
* Queued background jobs with status tracking
* Durable workflow checkpoints
* A background SLA monitoring service
* Pre-generated document embeddings
* Slack, Teams, and email integrations
* Application metrics, logs, and tracing
