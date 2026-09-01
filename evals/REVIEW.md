# Golden Set — Review Sheet

40 questions. **Check each answer against its cited source file.**
Tell me any row numbers that are wrong and I'll redraft them.
Nothing here is verified until you say so — an unverified golden set makes
every number downstream decorative.

## direct (12)

**0.** What is the full email format of the invoker service account created by the module? 
> <invoker_account_id>@<project_id>.iam.gserviceaccount.com
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

**21.** When a Nexus operation is started using the NexusOperationLogInterceptor, what details are logged, and what is the maximum number of Actions Per Second allowed for a provisioned capacity of 6 TRUs? 
> The interceptor logs the service name and operation name when the operation starts, and after the operation starts it logs the same service and operation along with whether the result is asynchronous (the 'async' flag). For a provisioned capacity of 6 TRUs, the maximum Actions Per Second is 500.
`cloud/capacity-modes.mdx,develop/typescript/workers/interceptors.mdx`

**22.** What mechanisms are used to detect dead or crashed Workers in Temporal workflows, and where can you find sample implementations of these mechanisms? 
> The workflow uses heartbeats (30 seconds) for fast crash detection and a schedule‑to‑start timeout (5 minutes) for dead‑worker detection; sample implementations of these patterns are provided in the pick‑first design‑pattern page with Go, TypeScript, Java, and Python sample repositories.
`guides/worker-execution-affinity.mdx,design-patterns/pick-first.mdx`

**23.** How can you run a workflow that uses standalone activities on Temporal Cloud when the task queue name cannot be defined as a constant across different client implementations? 
> You can keep the existing Worker and Client code (which uses Temporalio::EnvConfig::ClientConfig.load_client_connect_options) and configure the connection to Temporal Cloud via environment variables or a TOML profile, so no code changes are needed. For the task‑queue name, instead of a compile‑time constant, supply the name at runtime through configuration (e.g., an environment variable or a settings file) that both the client that starts the workflow and the worker can read, allowing the workflow to be started from a different system or language while still using the same standalone‑activity code.
`develop/ruby/activities/standalone-activities.mdx,encyclopedia/workers/task-queue-naming.mdx`

**24.** What is the initial version number for Cluster A in the version‑history example, and what prerequisite knowledge does the Strands Agents guide assume you have? 
> The initial version of Cluster A is 1, and the guide assumes you are already familiar with Strands Agents (and have basic knowledge of Temporal).
`production-deployment/self-hosted-guide/multi-cluster-replication.mdx,develop/typescript/integrations/strands-agents.mdx`

**25.** When a worker's task slots are exhausted (no new tasks can be picked up), which Temporal API call can still be used to retrieve workflow information, and is it permitted for all user roles listed in the permissions table? 
> The `QueryWorkflow` API call can still be used, and it is permitted (✅) for all three user roles shown in the table.
`troubleshooting/worker-capacity.mdx,cloud/manage-access/users.mdx`

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
`NO SOURCE — must be genuinely absent from the docs`

**33.** What is the home address of Temporal's CEO? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**34.** How many employees does Temporal Technologies have? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**35.** What was Temporal's revenue last quarter? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**36.** Which venture capital firm led Temporal's Series C? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**37.** What is the WiFi password at Temporal's head office? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**38.** What is our company's internal on-call escalation policy for Temporal? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`

**39.** How many Temporal workflows did Netflix run yesterday? 
> I don't know.
`NO SOURCE — must be genuinely absent from the docs`
