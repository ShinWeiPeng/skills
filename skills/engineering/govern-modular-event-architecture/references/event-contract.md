# Port and event contract

## Inputs

A command enters through a typed input port. Validate syntax and admission conditions before accepting it.

- Return an immediate rejection such as `invalid`, `busy`, or `unavailable` when work was not accepted.
- After acceptance, report completion or execution failure through the output event contract.
- Permit a side-effect-free query or pure calculation to return synchronously.

## Outputs

A functional module exposes one output sink. It does not own a subscriber collection. The parent or an adapter implements fan-out to zero or more subscribers.

Fan-out MUST:

1. invoke subscribers outside the producer's internal lock;
2. continue after one subscriber fails;
3. preserve deterministic configured order within a stream;
4. aggregate failures and publish them to the parent's error port;
5. avoid pretending that completed callbacks can be rolled back.

## Event envelope

Every cross-module event MUST declare these fields:

- `event_type`
- `source`
- `correlation_id`
- `stream_id`
- `sequence`
- `payload`

Timestamps are optional when no trustworthy clock exists. Persistent event IDs and retry metadata become mandatory for at-least-once delivery.

## Lifecycle

Core states:

`received -> validated -> processing -> succeeded | failed`

Reliability extension:

`accepted -> retrying -> cancelled | dead-letter`

The producer MUST commit its state before publishing success or failure. Processing of the same stream is serialized and non-reentrant. Different streams MAY run concurrently.

## Delivery

Every event contract declares `at-most-once` or `at-least-once`.

- Use `at-most-once` by default for in-process callbacks without retries.
- Use `at-least-once` when retries or persistence are enabled. Require a persistent event ID and an idempotency strategy.
- Do not claim exactly-once delivery without a project-specific proof and accepted ADR.

## C port shape

```c
typedef struct {
    void *context;
    SubmitResult (*submit)(void *context, const Command *command);
} InputPort;

typedef struct {
    void *context;
    PublishResult (*publish)(void *context, const Event *event);
} OutputPort;
```

The functional layer owns these types. An adapter supplies function pointers and context at the composition root.

