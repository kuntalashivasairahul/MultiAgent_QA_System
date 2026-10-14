# Reference review — revised dataset

40 development questions and 10 held-out confirmation questions. Source audit by the coding assistant against corpus commit 5b56ddca7d409a82f2d74e21f20edf35f29ad483; this is not a claim of independent human review.

Original references are preserved in history/golden_v1.jsonl. Revised questions name their SDK/example. Multihop comparisons require facts from each SDK-specific source; alternate paths are grouped as substitutes, not additional required sources.

The holdout is excluded from development runs. It was authored by the same assistant, and shares some topics with development data; it is a small confirmation set, not an independent blind benchmark.

## Development

### dev-00 (direct)

What is required to access the pre‑release Cloud Run support for Temporal Serverless Workers?

You must create a support ticket or contact your account team for access, and you can sign up for updates to hear when Cloud Run reaches Public Preview.

Evidence groups: [["production-deployment/worker-deployments/serverless-workers/cloud-run/index.mdx"]]

### dev-01 (direct)

What does Activity.wrap() return when it is given a checked exception?

It returns a CheckedExceptionWrapper around the checked exception.

Evidence groups: [["develop/java/best-practices/error-handling.mdx"]]

### dev-02 (direct)

In the Celery-to-Standalone-Activity migration guide, what command starts the Python Worker?

python worker.py

Evidence groups: [["guides/celery-to-standalone-activity.mdx"]]

### dev-03 (direct)

In the execution-failures troubleshooting guide, which metric tag identifies the failing Activity type?

The `activity_type` tag.

Evidence groups: [["troubleshooting/execution-failures.mdx"]]

### dev-04 (direct)

In the Java SDK, what function starts a new Workflow Run using Continue-As-New?

Workflow.continueAsNew()

Evidence groups: [["develop/java/workflows/continue-as-new.mdx"]]

### dev-05 (direct)

What command disables API key authentication for a Temporal Cloud namespace?

The `temporal cloud namespace api-key disable` command disables API key authentication for a Temporal Cloud namespace.

Evidence groups: [["cli/command-reference/cloud/namespace.mdx"]]

### dev-06 (direct)

In Temporal, how can a workflow be paused after activity retries are exhausted and later resumed with corrected input using a signal?

The workflow can be parked in a waiting state and block on a Signal; when the Signal arrives with corrected input from a human operator, the workflow re-executes the activity, resuming exactly where it left off.

Evidence groups: [["design-patterns/resumable-activity.mdx"]]

### dev-07 (direct)

What is the default value for max_concurrent_activities in the lambda_worker package?

2

Evidence groups: [["develop/python/workers/serverless-workers/aws-lambda.mdx"]]

### dev-08 (direct)

In the Python Google GenAI hello-world example, what task_queue name is used to execute the Workflow?

google-genai-hello-world

Evidence groups: [["develop/python/integrations/google-genai.mdx"]]

### dev-09 (direct)

In the Java Nexus feature-guide example, what mainClass argument starts the handler Worker?

io.temporal.samples.nexus.handler.HandlerWorker

Evidence groups: [["develop/java/nexus/feature-guide.mdx"]]

### dev-10 (direct)

In the Recover Without Restart guide, how often does its dashboard poll the web service?

Every 3 seconds.

Evidence groups: [["guides/recover-without-restart.mdx"]]

### dev-11 (direct)

Which command pulls the Temporal proxy container image?

docker pull temporalio/temporal-proxy:latest

Evidence groups: [["production-deployment/temporal-proxy/index.mdx"]]

### dev-12 (jargon)

What does the Parent Close Policy determine in Temporal?

It determines what happens to a Child Workflow Execution when its Parent Workflow Execution changes to a Closed status (Completed, Failed, or Timed out).

Evidence groups: [["glossary.md", "encyclopedia/child-workflows/parent-close-policy.mdx"]]

### dev-13 (jargon)

What responsibilities does the Frontend Service have in Temporal?

The Frontend Service is a stateless gateway that handles rate limiting, authorization, validation, and routing of all inbound calls.

Evidence groups: [["glossary.md", "encyclopedia/temporal-service/temporal-server.mdx"]]

### dev-14 (jargon)

What is the definition of the Temporal-specific term "Retention Period"?

A Retention Period is the amount of time a Workflow Execution Event History remains in the Temporal Service's persistence store.

Evidence groups: [["glossary.md", "encyclopedia/temporal-service/temporal-server.mdx"]]

### dev-15 (jargon)

What components make up a Temporal Service?

A Temporal Service consists of a Temporal Server paired with Persistence and Visibility stores.

Evidence groups: [["glossary.md", "encyclopedia/temporal-service/temporal-service.mdx"]]

### dev-16 (jargon)

What is a Local Activity in Temporal?

A Local Activity is an Activity Execution that executes in the same process as the Workflow Execution that spawns it.

Evidence groups: [["glossary.md", "encyclopedia/activities/local-activity.mdx"]]

### dev-17 (jargon)

What does the term Visibility refer to within the Temporal Platform?

It refers to the subsystems and APIs that enable an operator to view Workflow Executions that currently exist within a Temporal Service.

Evidence groups: [["glossary.md", "encyclopedia/temporal-service/visibility.mdx"]]

### dev-18 (jargon)

What are Dynamic Handlers in Temporal?

Dynamic Handlers are Workflows, Activities, Signals, or Queries that are unnamed and invoked when no other named handler matches the call from the Server at runtime.

Evidence groups: [["glossary.md", "encyclopedia/workflow/dynamic-handler.mdx"]]

### dev-19 (jargon)

What does the Nexus Registry manage, and how are its scope and Endpoint-name uniqueness defined for Cloud versus self-hosted deployments?

It manages Nexus Endpoints. Endpoint names must be unique within the Registry. In Temporal Cloud the Registry spans the Account and all its Namespaces; self-hosted it is scoped to a Cluster.

Evidence groups: [["glossary.md", "encyclopedia/nexus/nexus-registry.mdx"]]

### dev-20 (multihop)

When porting Continue-As-New logic between Java and Python Temporal Workflows, what function starts the new Run in each SDK?

Java uses Workflow.continueAsNew(); Python uses workflow.continue_as_new().

Evidence groups: [["develop/java/workflows/continue-as-new.mdx"], ["develop/python/workflows/continue-as-new.mdx"]]

### dev-21 (multihop)

How do the Go and TypeScript external-storage prerequisite documents differ in their stated read/write permissions for storing payloads?

Both require write permission for storing and read permission for retrieving. The Go document explicitly says storing also requires read permission because drivers check for an existing object. The TypeScript document says retrieve-only components do not need write access and the reverse is also true; it does not state the Go additional-read requirement.

Evidence groups: [["develop/go/best-practices/data-handling/external-storage.mdx"], ["develop/typescript/best-practices/data-handling/external-storage.mdx"]]

### dev-22 (multihop)

When monitoring whether Continue-As-New is suggested, which SDK call should a Java Workflow use and which should a Python Workflow use?

Java uses Workflow.getInfo().isContinueAsNewSuggested(); Python uses workflow.info().is_continue_as_new_suggested().

Evidence groups: [["develop/java/workflows/continue-as-new.mdx"], ["develop/python/workflows/continue-as-new.mdx"]]

### dev-23 (multihop)

In Java, how does a client invoke a Dynamic Workflow, and what method and input type must its implementation provide?

The client calls the Dynamic Workflow using an untyped WorkflowStub (as shown in the client code) and the workflow implementation must be registered with the worker (e.g., worker.registerWorkflowImplementationTypes(...)). The implementation must extend DynamicWorkflow and provide the execute method, which receives EncodedValues as the inputs to the Workflow Execution.

Evidence groups: [["develop/java/client/temporal-client.mdx"], ["develop/java/workflows/message-passing.mdx"]]

### dev-24 (multihop)

To let a Child Workflow survive its parent closing, which Parent Close Policy field/parameter and ABANDON value are used in Go and Python?

Go sets workflow.ChildWorkflowOptions.ParentClosePolicy to enums.PARENT_CLOSE_POLICY_ABANDON. Python sets parent_close_policy to ParentClosePolicy.ABANDON in start_child_workflow or execute_child_workflow.

Evidence groups: [["develop/go/workflows/child-workflows.mdx"], ["develop/python/workflows/child-workflows.mdx"]]

### dev-25 (multihop)

For a Workflow constructor to receive Workflow input before message handlers run, what initializer marker is used in PHP versus Java?

PHP uses the #[WorkflowInit] attribute; Java uses the @WorkflowInit annotation.

Evidence groups: [["develop/php/workflows/message-passing.mdx"], ["develop/java/workflows/message-passing.mdx"]]

### dev-26 (multihop)

When listing standalone Nexus operations matching a filter, which base-client methods are used in .NET versus Go?

.NET uses ITemporalClient.ListNexusOperationsAsync(); Go uses client.ListNexusOperations(). These are on the base Temporal client, not the NexusClient.

Evidence groups: [["develop/dotnet/nexus/standalone-operations.mdx"], ["develop/go/nexus/standalone-operations.mdx"]]

### dev-27 (multihop)

What are the method names used in the .NET and Go SDKs to count standalone Nexus operations?

In the .NET SDK the method is `ITemporalClient.CountNexusOperationsAsync()`, and in the Go SDK the method is `client.CountNexusOperations()`.

Evidence groups: [["develop/dotnet/nexus/standalone-operations.mdx"], ["develop/go/nexus/standalone-operations.mdx"]]

### dev-28 (ambiguous)

Why are some scheduled workflow actions being skipped or delayed even though they were supposed to run?

Because the schedule’s catch‑up window was exceeded—either the service or namespace was down longer than the one‑year default, the namespace hit rate‑limiting causing starts to be throttled, or long‑running executions under BufferAll caused buffer overruns that pushed actions past the catch‑up window.

Evidence groups: [["troubleshooting/schedule-missed-actions.mdx"]]

### dev-29 (ambiguous)

In the Go upgrade-on-continue-as-new example, how can a Workflow detect and adopt a changed target Worker deployment version?

By periodically checking the GetTargetWorkerDeploymentVersionChanged flag—e.g., after a short workflow.Sleep that triggers a new workflow task—and, when the flag is true, returning a ContinueAsNew error with AutoUpgrade versioning behavior.

Evidence groups: [["production-deployment/worker-deployments/worker-versioning/upgrade-on-continue-as-new.mdx"]]

### dev-30 (ambiguous)

Is it possible to eliminate a workflow that only triggers one Nexus operation and call the operation directly?

Yes. When a workflow's sole purpose is to invoke a single Nexus operation, you can drop that workflow and invoke the operation as a standalone Nexus operation. Just keep the workflow if it does additional work, choose a stable operation ID for deduplication, and update any visibility queries that relied on workflow attributes.

Evidence groups: [["encyclopedia/nexus/standalone-nexus-operation.mdx"]]

### dev-31 (ambiguous)

In Go Workflow tests, how can I mock Nexus asynchronous operations and add custom synchronous operation logic?

You can mock each Nexus asynchronous operation with a separate operation token and register its completion result, and if you need custom behavior you define a SyncOperation with your own function, register it in a Nexus service, and add that service to the test environment.

Evidence groups: [["develop/go/best-practices/testing-suite.mdx"]]

### dev-32 (unanswerable)

How much does Temporal Cloud cost per million actions?

I don't know.

Evidence groups: []

### dev-33 (unanswerable)

What is the home address of Temporal's CEO?

I don't know.

Evidence groups: []

### dev-34 (unanswerable)

How many employees does Temporal Technologies have?

I don't know.

Evidence groups: []

### dev-35 (unanswerable)

What was Temporal's revenue last quarter?

I don't know.

Evidence groups: []

### dev-36 (unanswerable)

Which venture capital firm led Temporal's Series C?

I don't know.

Evidence groups: []

### dev-37 (unanswerable)

What is the WiFi password at Temporal's head office?

I don't know.

Evidence groups: []

### dev-38 (unanswerable)

What is our company's internal on-call escalation policy for Temporal?

I don't know.

Evidence groups: []

### dev-39 (unanswerable)

How many Temporal workflows did Netflix run yesterday?

I don't know.

Evidence groups: []

## Holdout

### holdout-00 (direct)

What is the minimum Namespace Retention Period permitted by the documented Temporal Service?

1 day.

Evidence groups: [["encyclopedia/temporal-service/temporal-server.mdx"]]

### holdout-01 (direct)

For Sticky Execution, what is the default time within which a Worker must start a Sticky Queue Workflow Task before stickiness is disabled?

Five seconds.

Evidence groups: [["encyclopedia/workers/sticky-execution.mdx"]]

### holdout-02 (jargon)

What is a Sticky Queue, and which Worker polls it?

An automatically named Worker-specific Task Queue shared exclusively with the Worker that first picked up the Workflow Task; that Worker polls it alongside the original queue.

Evidence groups: [["encyclopedia/workers/sticky-execution.mdx"]]

### holdout-03 (jargon)

What does an Activity Execution consist of in Temporal?

The full chain of Activity Task Executions.

Evidence groups: [["encyclopedia/activities/activity-execution.mdx"]]

### holdout-04 (multihop)

Which Go and Python Workflow APIs allow specifying a Parent Close Policy for Child Workflows?

Go uses the ParentClosePolicy field of workflow.ChildWorkflowOptions. Python uses the parent_close_policy parameter of start_child_workflow or execute_child_workflow.

Evidence groups: [["develop/go/workflows/child-workflows.mdx"], ["develop/python/workflows/child-workflows.mdx"]]

### holdout-05 (multihop)

Before Continue-As-New, how do Java and Python Workflows check whether the server suggests starting a new Run?

Java uses Workflow.getInfo().isContinueAsNewSuggested(); Python uses workflow.info().is_continue_as_new_suggested().

Evidence groups: [["develop/java/workflows/continue-as-new.mdx"], ["develop/python/workflows/continue-as-new.mdx"]]

### holdout-06 (ambiguous)

Why did a Workflow Task return to the ordinary queue after its Sticky Queue Worker was slow to start it?

If the Worker does not start the task within the Sticky Schedule-To-Start timeout (five seconds by default), the service disables stickiness and reschedules the task in the original Task Queue.

Evidence groups: [["encyclopedia/workers/sticky-execution.mdx"]]

### holdout-07 (ambiguous)

I shortened Namespace retention, but old closed Workflows did not disappear sooner. Why?

A changed Retention Period applies to executions closing after the change; already closed executions keep their original cleanup timers.

Evidence groups: [["encyclopedia/temporal-service/temporal-server.mdx"]]

### holdout-08 (unanswerable)

Which Temporal Namespace is used by our private Acme payroll production Worker?

I don't know.

Evidence groups: []

### holdout-09 (unanswerable)

What retry policy is configured in our private Acme billing Workflow repository?

I don't know.

Evidence groups: []
