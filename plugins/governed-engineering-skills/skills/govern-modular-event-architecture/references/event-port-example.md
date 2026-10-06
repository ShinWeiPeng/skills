# C event port example

Illustrates FLOW-INPUT-001 and FLOW-OUTPUT-001; synchronous completion follows API-COMPLETE-001.

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

The functional layer owns these types (MOD-DEP-006). An adapter supplies function
pointers and context at the composition root (MOD-DEP-004).
