# Golden Set — Review Sheet

40 questions. Check each answer against its cited source.
Rows 0 and 21-25 were redrafted after the first review found fabrications.

## direct (12)

**0.** What is required to access the pre‑release Cloud Run support for Temporal Serverless Workers? 
> You must create a support ticket or contact your account team for access, and you can sign up for updates to hear when Cloud Run reaches Public Preview.
`production-deployment/worker-deployments/serverless-workers/cloud-run/index.mdx`

**1.** What does Activity.wrap() return when it is given a checked exception? 
> It returns a CheckedExceptionWrapper around the checked exception.
`develop/java/best-practices/error-handling.mdx`

**2.** What command is used to start the Worker? 
> python worker.py
`guides/celery-to-standalone-activity.mdx`

**3.** What tag narrows down which Activity is failing? 
> The `activity_type` tag.
`troubleshooting/execution-failures.mdx`

**4.** What function is called inside the Workflow to start a new run when using Continue-As-New? 
> Workflow.continueAsNew()
`develop/java/workflows/continue-as-new.mdx`

**5.** What command disables API key authentication for a Temporal Cloud namespace? 
> The `temporal cloud namespace api-key disable` command disables API key authentication for a Temporal Cloud namespace.
`cli/command-reference/cloud/namespace.mdx`

**6.** In Temporal, how can a workflow be paused after activity retries are exhausted and later resumed with corrected input using a signal? 
> The workflow can be parked in a waiting state and block on a Signal; when the Signal arrives with corrected input from a human operator, the workflow re-executes the activity, resuming exactly where it left off.
`design-patterns/resumable-activity.mdx`

**7.** What is the default value for max_concurrent_activities in the lambda_worker package? **[answer too short]**
> 2
`develop/python/workers/serverless-workers/aws-lambda.mdx`

**8.** What is the task queue name used when executing the workflow? 
> google-genai-hello-world
`develop/python/integrations/google-genai.mdx`

**9.** What is the mainClass argument used to run the handler Worker? 
> io.temporal.samples.nexus.handler.HandlerWorker
`develop/java/nexus/feature-guide.mdx`

**10.** How often does the dashboard poll the web service? 
> Every 3 seconds.
`guides/recover-without-restart.mdx`

**11.** Which command pulls the Temporal proxy container image? 
> docker pull temporalio/temporal-proxy:latest
`production-deployment/temporal-proxy/index.mdx`

## jargon (8)

**12.** What does the Parent Close Policy determine in Temporal? 
> It determines what happens to a Child Workflow Execution when its Parent Workflow Execution changes to a Closed status (Completed, Failed, or Timed out).
`glossary.md`

**13.** What responsibilities does the Frontend Service have in Temporal? 
> The Frontend Service is a stateless gateway that handles rate limiting, authorization, validation, and routing of all inbound calls.
`glossary.md`

**14.** What is the definition of the Temporal-specific term "Retention Period"? 
> A Retention Period is the amount of time a Workflow Execution Event History remains in the Temporal Service's persistence store.
`glossary.md`

**15.** What components make up a Temporal Service? 
> A Temporal Service consists of a Temporal Server paired with Persistence and Visibility stores.
`glossary.md`

**16.** What is a Local Activity in Temporal? 
> A Local Activity is an Activity Execution that executes in the same process as the Workflow Execution that spawns it.
`glossary.md`

**17.** What does the term Visibility refer to within the Temporal Platform? 
> It refers to the subsystems and APIs that enable an operator to view Workflow Executions that currently exist within a Temporal Service.
`glossary.md`

**18.** What are Dynamic Handlers in Temporal? 
> Dynamic Handlers are Workflows, Activities, Signals, or Queries that are unnamed and invoked when no other named handler matches the call from the Server at runtime.
`glossary.md`

**19.** What is the Nexus Registry in Temporal? 
> The Nexus Registry manages Nexus Endpoints and provides lookup services for resolving Nexus requests at runtime; in the open‑source version it is scoped to a Cluster, in Temporal Cloud it is scoped to an Account, endpoint names must be unique, and the Temporal Service uses it to resolve a request’s Endpoint to a Namespace and Task Queue.
`glossary.md`

## multihop (8)

**20.** What permission is required to manage a Namespace‑scoped service account, and which Temporal component provides the APIs that a developer would use to interact with the Temporal Service when performing such management tasks? 
> Managing a Namespace‑scoped service account requires the Namespace Admin permission on that namespace, and a developer would use the Temporal SDK, which offers APIs to communicate with the Temporal Service.
`cloud/manage-access/permissions-reference.mdx,glossary.md`

**21.** What permissions are needed for processes/components that store payloads versus those that retrieve payloads, according to the Go and TypeScript external storage prerequisites? 
> Permission to write objects on processes that store payloads, and to read objects on processes that retrieve them. Storing also requires read permission, because the drivers check whether an object already exists before uploading. Components that only retrieve payloads do not need write access, and the reverse is also true.
`develop/go/best-practices/data-handling/external-storage.mdx,develop/typescript/best-practices/data-handling/external-storage.mdx`

**22.** According to the documentation, which signals should be used to monitor a Task Queue backlog and worker saturation, and what does the Datadog OpenMetrics integration monitor? 
> To monitor Tasks backing up in a Task Queue, use Cloud metrics plus SDK Schedule-To-Start metrics. To monitor Workers saturated, under‑provisioned, or misconfigured, use SDK metrics. The Datadog OpenMetrics integration lets you use OpenMetrics in Datadog to monitor Temporal Cloud behavior such as Task Queue backlog, poll success, and rate limiting, and you can collect SDK metrics from your Workers separately to monitor saturation, Schedule-To-Start latency, slot availability, and sticky cache behavior.
`cloud/metrics/openmetrics/metrics-integrations.mdx,cloud/metrics/index.mdx`

**23.** How does a client invoke a Dynamic Workflow implementation and what method must the workflow implementation provide to handle inputs? 
> The client calls the Dynamic Workflow using an untyped WorkflowStub (as shown in the client code) and the workflow implementation must be registered with the worker (e.g., worker.registerWorkflowImplementationTypes(...)). The implementation must extend DynamicWorkflow and provide the execute method, which receives EncodedValues as the inputs to the Workflow Execution.
`develop/java/client/temporal-client.mdx,develop/java/workflows/message-passing.mdx`

**24.** What must an Activity do to be able to receive a cancellation request, and what are the Cancelled Failure messages for a missed heartbeat timeout and for a workflow that has reached a Closed state? 
> The Activity Execution must send Heartbeats and set a Heartbeat Timeout; if the Heartbeat is not invoked, the Activity cannot receive a cancellation request. If the Server didn’t receive a heartbeat within the Activity’s Heartbeat timeout, the Cancelled Failure will have message: 'TIMED_OUT'. If the Workflow Run reached a Closed state, the Cancelled Failure will have message: 'NOT_FOUND'.
`encyclopedia/activities/activity-execution.mdx,develop/typescript/workflows/cancellation.mdx`

**25.** What command retrieves the current mTLS authentication configuration for a Temporal Cloud namespace, and which flag can be used to authenticate with an API key instead of interactive login? 
> Use the command `temporal cloud namespace mtls get --namespace my-namespace.my-account`; you can add the `--api-key` flag (a string API key) to authenticate with Temporal Cloud instead of interactive login.
`cli/command-reference/cloud/namespace.mdx,cloud/get-started/namespaces.mdx`

**26.** When setting up a GCP Private Service Connect endpoint for a Temporal workflow that uses the `Patched` marker feature flag, which endpoint option must be enabled to allow workers outside the selected region to connect, and what does the `Patched` marker guarantee during workflow replay? 
> You must enable **Enable global access** on the endpoint (which requires the network routing mode to be set to GLOBAL) to let workers outside the region connect. The `Patched` marker guarantees that, during replay, a workflow task will fail if the current code does not produce the same patch marker, ensuring the feature‑flag behavior is consistent between pre‑patch and post‑patch versions.
`develop/dotnet/workflows/versioning.mdx,cloud/connectivity/gcp-connectivity.mdx`

**27.** When using the Continue‑As‑New helper to roll over a workflow that contains large payloads, how can the carried state be kept small, and which Temporal CLI command creates a new default Build ID for the task queue that will run the new workflow version? 
> Offload the large payloads to external storage so each item is a small reference and apply truncation to drop entries already consumed; the CLI command is `temporal task-queue update-build-ids add-new-default` (with appropriate flags).
`encyclopedia/workflow-message-passing/workflow-streams.mdx,cli/command-reference/task-queue.mdx`

## ambiguous (4)

**28.** Why are some scheduled workflow actions being skipped or delayed even though they were supposed to run? 
> Because the schedule’s catch‑up window was exceeded—either the service or namespace was down longer than the one‑year default, the namespace hit rate‑limiting causing starts to be throttled, or long‑running executions under BufferAll caused buffer overruns that pushed actions past the catch‑up window.
`troubleshooting/schedule-missed-actions.mdx`

**29.** How can a workflow detect that the target worker deployment version has changed? 
> By periodically checking the GetTargetWorkerDeploymentVersionChanged flag—e.g., after a short workflow.Sleep that triggers a new workflow task—and, when the flag is true, returning a ContinueAsNew error with AutoUpgrade versioning behavior.
`production-deployment/worker-deployments/worker-versioning/upgrade-on-continue-as-new.mdx`

**30.** Is it possible to eliminate a workflow that only triggers one Nexus operation and call the operation directly? 
> Yes. When a workflow's sole purpose is to invoke a single Nexus operation, you can drop that workflow and invoke the operation as a standalone Nexus operation. Just keep the workflow if it does additional work, choose a stable operation ID for deduplication, and update any visibility queries that relied on workflow attributes.
`encyclopedia/nexus/standalone-nexus-operation.mdx`

**31.** How can I mock Nexus operations in a workflow test and add custom logic to them? 
> You can mock each Nexus asynchronous operation with a separate operation token and register its completion result, and if you need custom behavior you define a SyncOperation with your own function, register it in a Nexus service, and add that service to the test environment.
`develop/go/best-practices/testing-suite.mdx`

## unanswerable (8)

**32.** How much does Temporal Cloud cost per million actions? 
> I don't know.
`NO SOURCE`

**33.** What is the home address of Temporal's CEO? 
> I don't know.
`NO SOURCE`

**34.** How many employees does Temporal Technologies have? 
> I don't know.
`NO SOURCE`

**35.** What was Temporal's revenue last quarter? 
> I don't know.
`NO SOURCE`

**36.** Which venture capital firm led Temporal's Series C? 
> I don't know.
`NO SOURCE`

**37.** What is the WiFi password at Temporal's head office? 
> I don't know.
`NO SOURCE`

**38.** What is our company's internal on-call escalation policy for Temporal? 
> I don't know.
`NO SOURCE`

**39.** How many Temporal workflows did Netflix run yesterday? 
> I don't know.
`NO SOURCE`
