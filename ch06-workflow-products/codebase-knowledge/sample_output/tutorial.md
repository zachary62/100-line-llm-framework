# Chapter 1: BaseNode

Welcome to the first chapter of the PocketFlow tutorial! In this chapter, we will explore **`BaseNode`**, the foundational unit of execution that powers everything in PocketFlow. 

Whether you are building a simple script or a complex multi-step workflow, understanding `BaseNode` is essential because every node in PocketFlow inherits its core behavior from this class.

---

## What is a `BaseNode`?

At its core, a `BaseNode` represents a single step of work. To keep your code clean, modular, and easy to reason about, PocketFlow divides the work of a single node into three distinct lifecycle phases:
1. **`prep` (Prepare):** Gathers or formats the data needed for the task.
2. **`exec` (Execute):** Performs the actual heavy lifting or core logic using the prepared data.
3. **`post` (Post-process):** Handles cleanup, updates shared state, or returns a specific action signal to determine what happens next.

Here is how `BaseNode` is defined in the source code:

```python
class BaseNode:
    def __init__(self): self.params,self.successors={},{}
    def set_params(self,params): self.params=params
    def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node
    def prep(self,shared): pass
    def exec(self,prep_res): pass
    def post(self,shared,prep_res,exec_res): pass
    def _exec(self,prep_res): return self.exec(prep_res)
    def _run(self,shared): p=self.prep(shared); e=self._exec(p); return self.post(shared,p,e)
    def run(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use Flow.")  
        return self._run(shared)
    def __rshift__(self,other): return self.next(other)
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")
```

---

## Breaking Down the Lifecycle Methods

When a node executes, it flows through an internal helper method called `_run(shared)`, which orchestrates the three main lifecycle hooks in order:

```python
    def _run(self,shared): 
        p = self.prep(shared) 
        e = self._exec(p) 
        return self.post(shared, p, e)
```

1. **`prep(shared)`**: This method receives a `shared` dictionary (representing the global state of your application or workflow). It pulls out whatever data this specific node needs.
2. **`exec(prep_res)`**: This method takes the output of `prep` (`prep_res`) and runs the core logic. By separating `prep` from `exec`, your execution logic remains pure and focused entirely on computation.
3. **`post(shared, prep_res, exec_res)`**: This method receives the shared state, the preparation results, and the execution results. It can update the `shared` state or return a string action (like `"success"` or `"retry"`) to dictate the flow of the program.

By default, these methods (`prep`, `exec`, and `post`) do nothing (`pass`). You customize a node's behavior by subclassing `BaseNode` and overriding these methods.

---

## Connecting Nodes Together

`BaseNode` also includes built-in mechanisms for linking nodes together into chains or graphs using the `next()` method or Python's bitwise shift operators (`>>` and `-`):

* **`node1 >> node2`**: Links `node1` to `node2` using the default action.
* **`node1 - "action" >> node2`**: Sets up a conditional transition, meaning `node2` will only run if `node1`'s `post` method returns `"action"`.

```python
    def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node

    def __rshift__(self,other): return self.next(other)
```

*(Note: If you attempt to call `.run()` directly on a node that has successors connected to it, PocketFlow will issue a warning reminding you that individual nodes don't execute successors—you need a `Flow` for that, which we will cover in later chapters!)*

---

## Chapter Summary

The `BaseNode` serves as the foundational building block of PocketFlow by enforcing a clean, predictable execution lifecycle split into `prep`, `exec`, and `post` phases. By subclassing `BaseNode` and overriding these hook methods, you can easily encapsulate discrete units of logic while utilizing built-in operators like `>>` to map out how data and execution flow from one step to the next.

---

# Chapter: _ConditionalTransition

Welcome to the next chapter of the PocketFlow tutorial! In the previous chapter, we explored `BaseNode` and learned how individual steps of work are structured. But building a workflow isn't just about single steps—it's about connecting those steps together so data can flow from one node to the next. 

In this chapter, we will look at **`_ConditionalTransition`**, a clever helper class that brings elegant syntactic sugar to PocketFlow for routing between nodes based on specific actions.

---

## The Problem: Connecting Nodes

Normally, when you link one node to another, it happens unconditionally. For example, using the right-shift operator (`>>`) you might write:

```python
node_a >> node_b
```

This tells PocketFlow: *"When `node_a` finishes, move straight to `node_b`."*

However, real-world workflows often require decision-making. What if `node_a` needs to route to `node_b` if a check passes, but route to `node_c` if it fails? PocketFlow handles this by allowing nodes to return an **action string** (like `"success"` or `"failure"`) during their execution phase, which the flow engine then uses to decide the next step.

## Enter `_ConditionalTransition`

To make setting up these conditional paths clean and readable without writing verbose method calls, PocketFlow overloads the subtraction operator (`-`) using the `__sub__` method in `BaseNode`, paired with the `_ConditionalTransition` class.

Let's look at the source code for both parts:

```python
class BaseNode:
    # ... other methods ...
    def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node

    def __rshift__(self,other): return self.next(other)
    
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")

class _ConditionalTransition:
    def __init__(self,src,action): self.src,self.action=src,action
    def __rshift__(self,tgt): return self.src.next(tgt,self.action)
```

### How It Works Under the Hood

1. **The Subtraction Operator (`__sub__`):** When you write `node_a - "success"`, Python invokes the `__sub__` method on `node_a` with the string `"success"`. 
2. **Creating the Helper:** Instead of performing arithmetic, `BaseNode.__sub__` checks if the argument is a string and returns a temporary `_ConditionalTransition` object. This object holds onto a reference of the source node (`src`) and the action name (`action`).
3. **Completing the Route (`__rshift__`):** Next, you chain the right-shift operator onto that temporary object, like this: `node_a - "success" >> node_b`. This triggers the `__rshift__` method inside `_ConditionalTransition`, which calls `src.next(tgt, self.action)`. 

Ultimately, this registers `node_b` as the successor of `node_a` specifically when `node_a` produces the `"success"` action.

## Why is it designed this way?

PocketFlow is designed to make defining complex workflows feel as natural as writing regular Python code. By leveraging Python's operator overloading (`-` and `>>`), `_ConditionalTransition` lets you chain conditional routes fluidly in a single line of code—turning what could have been clunky configuration dictionaries or verbose builder patterns into readable, expressive syntax.

---

In summary, `_ConditionalTransition` is an invisible yet powerful helper class that acts as a bridge between Python's operators and PocketFlow's routing system. By combining the subtraction operator with right-shift chaining (e.g., `node - "action" >> target`), it enables developers to map out conditional workflows intuitively and concisely.

---

# Chapter: Node

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build single steps of work using `BaseNode` and how to connect them using routing syntax. However, real-world applications are messy. Network requests time out, APIs throw errors, and databases occasionally drop connections. 

If a single step fails, you don't necessarily want your entire workflow to crash immediately. You need a way to retry operations automatically or handle failures gracefully. In this chapter, we will explore **`Node`**, an extension of `BaseNode` that adds built-in error handling, retry logic, and fallback mechanisms.

---

## What is a `Node`?

While `BaseNode` provides the basic structure for a task (`prep`, `exec`, and `post`), a standard `Node` wraps your execution logic with safety nets. It allows you to specify:
1. **`max_retries`**: How many times to attempt the execution before giving up.
2. **`wait`**: How many seconds to pause between retry attempts.
3. **`exec_fallback`**: A safety net method that runs if all retries fail.

Here is how `Node` is implemented in PocketFlow:

```python
class Node(BaseNode):
    def __init__(self, max_retries=1, wait=0):
        super().__init__()
        self.max_retries = max_retries
        self.wait = wait

    def exec_fallback(self, prep_res, exc):
        raise exc

    def _exec(self, prep_res):
        for self.cur_retry in range(self.max_retries):
            try:
                return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0:
                    time.sleep(self.wait)
```

### How It Works

* **The Retry Loop:** Inside `_exec`, PocketFlow loops up to `max_retries`. If `self.exec(prep_res)` succeeds, it returns the result immediately.
* **Catching Exceptions:** If an exception is raised, it catches the error (`except Exception as e:`). If it hasn't reached the final retry attempt, it waits for the specified number of seconds (`time.sleep(self.wait)`) before trying again.
* **The Fallback:** If *all* retries fail (i.e., we are on the final retry attempt), it delegates handling to `exec_fallback(prep_res, e)`. By default, this simply re-raises the exception (`raise exc`), but you can override it to return a default value or trigger an alternative action.

---

## Putting It Into Practice

Let’s look at how you might use a `Node` to handle an unreliable operation, such as fetching data from an external API that occasionally fails:

```python
import time
from pocketflow import Node

class FetchDataNode(Node):
    def exec(self, prep_res):
        print("Attempting to fetch data...")
        # Simulate a flaky API that fails sometimes
        raise ConnectionError("API is down!")

    def exec_fallback(self, prep_res, exc):
        print(f"All retries failed due to: {exc}. Using cached fallback data.")
        return {"data": "fallback_cache"}

# Create a node that tries 3 times, waiting 1 second between attempts
flaky_node = FetchDataNode(max_retries=3, wait=1)

# Run the node
result = flaky_node.run({})
print("Final Result:", result)
```

### Why Is It Designed This Way?

By baking retries and fallbacks directly into the `Node` class rather than forcing you to write `try/except` blocks inside every custom function, PocketFlow keeps your business logic clean. You focus entirely on *what* the task does in `exec()`, while configuration parameters like `max_retries` handle *how resilient* the task should be.

---

## Summary

In this chapter, we explored **`Node`**, a powerful subclass of `BaseNode` designed to make workflows robust against failure. By configuring `max_retries`, `wait` intervals, and custom `exec_fallback` behaviors, you can easily build fault-tolerant steps into your pipelines. In the next chapter, we will build upon this foundation to see how we can process collections of data concurrently or sequentially using batch nodes.

---

# Chapter: BatchNode

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build individual steps using `BaseNode`, connect them with routing syntax, and make them robust against failures using `Node`. 

However, real-world data is rarely processed purely as isolated, single items. Very often, you encounter collections—a list of files to process, a batch of user records to update, or a sequence of queries to run. Writing manual `for` loops inside your node logic can clutter your code and mix iteration concerns with business logic. 

In this chapter, we will explore **`BatchNode`**, a specialized node designed to automatically iterate over a collection of items and execute your core logic sequentially for each one.

---

## What is a `BatchNode`?

`BatchNode` inherits directly from `Node`, meaning it retains all the powerful retry and error-handling capabilities you learned about previously. But it adds a specific superpower: it overrides the internal execution method (`_exec`) to handle lists or collections natively.

Let's look at how it is implemented in the source code:

```python
class BatchNode(Node):
    def _exec(self,items): return [super(BatchNode,self)._exec(i) for i in (items or [])]
```

### How the Code Works

1. **Input Handling (`items or []`)**: The method safely checks if the input `items` (provided by `prep`) evaluates to `None` or empty. If it is empty or falsy, it defaults to an empty list `[]` to prevent runtime errors.
2. **Iteration**: It loops through every single item in the collection.
3. **Delegation to `Node` (`super(...)`)**: For each individual item `i`, it calls the parent class's `_exec(i)` method. This is brilliant because it means **every single item in the batch gets its own retry mechanism and fallback handling** if it fails!
4. **Result Aggregation**: It collects the results of each execution into a brand-new list and returns them all together.

---

## Why is it Designed This Way?

By separating the iteration logic from the core business logic, PocketFlow keeps your code clean and modular:

* **Automatic Resiliency per Item**: Because `BatchNode` delegates down to `Node._exec(i)`, if you configure your `BatchNode` with `max_retries=3`, *each individual item* in your batch gets up to 3 retry attempts independently. A failure in item #2 won't prevent item #3 from trying its best.
* **Declarative Collections**: Your `prep` method simply needs to return a list of items. The `BatchNode` automatically unpacks and maps them through your `exec` function.

---

## Summary

In this chapter, we introduced `BatchNode`, a specialized building block in PocketFlow that takes the heavy lifting out of processing collections. By automatically iterating over a list of items and routing each one through the robust, retry-enabled execution pipeline of a standard `Node`, `BatchNode` allows you to handle batch operations cleanly, safely, and with minimal boilerplate code.

---

# Chapter: Flow

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build single steps (`BaseNode`, `Node`), process collections of items (`BatchNode`), and link nodes together using routing syntax (`_ConditionalTransition`). 

However, as your applications grow, executing steps one by one manually becomes unmanageable. You need a way to encapsulate a whole web of connected nodes into a single, cohesive unit. In this chapter, we will explore **`Flow`**, a container Node that orchestrates multiple nodes into a sequential graph based on actions returned during execution.

---

## What is a `Flow`?

A `Flow` is itself a subclass of `BaseNode`, which means it can be treated just like any other node. But while a regular node performs a specific task, a `Flow` performs *orchestration*. It maintains a starting node, tracks the current execution step, inspects the action returned by that step, and looks up the successor node to run next.

Let's look at how the core orchestration engine is implemented in the source code:

```python
class Flow(BaseNode):
    def __init__(self,start=None): super().__init__(); self.start_node=start
    def start(self,start): self.start_node=start; return start
    def get_next_node(self,curr,action):
        nxt=curr.successors.get(action or "default")
        if not nxt and curr.successors: warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    def _orch(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: 
            curr.set_params(p)
            last_action=curr._run(shared) 
            curr=copy.copy(self.get_next_node(curr,last_action))
        return last_action
    def _run(self,shared): p=self.prep(shared); o=self._orch(shared); return self.post(shared,p,o)
    def post(self,shared,prep_res,exec_res): return exec_res
```

### Understanding the Code

1. **`start(start)`**: This helper method defines the entry point of your flow graph. It registers the initial node where execution begins.
2. **`get_next_node(curr, action)`**: When a node finishes running, it returns an `action` string (such as `"success"`, `"retry"`, or the default `"default"`). This method checks the current node's successors dictionary to find the corresponding next node. If the action isn't found, it gracefully warns the user that the flow is ending.
3. **`_orch(...)` (The Orchestrator Loop)**: This is the heartbeat of the `Flow`. It runs a `while curr:` loop that:
   - Sets runtime parameters on the current node.
   - Executes the current node (`curr._run(shared)`) and captures its return value as `last_action`.
   - Looks up and transitions to the next node based on that action.
4. **`_run(shared)`**: Like any `BaseNode`, a `Flow` can be executed. It calls its own `prep` method, triggers the orchestration loop, and finishes with a `post` method.

---

## Why is it Designed This Way?

The `Flow` pattern is designed around **composition and encapsulation**:

- **Nesting**: Because `Flow` inherits from `BaseNode`, a `Flow` can contain other `Flow` instances. You can build complex, hierarchical architectures by nesting smaller sub-flows inside larger parent flows.
- **Decoupled Control Flow**: Individual nodes don't need to know *where* they fit into the global application. A node simply performs its logic and returns an action string (e.g., `"approved"` or `"rejected"`). The `Flow` container reads that action and routes execution accordingly. This keeps your business logic clean and modular.
- **Shared State (`shared`)**: Throughout the orchestration loop, all nodes share access to a common `shared` state dictionary, making it easy to pass data implicitly from step to step across the graph.

---

## Summary

In this chapter, we explored **`Flow`**, the powerful container node that turns isolated steps into an orchestrated execution graph. By maintaining a starting point, evaluating return actions, and looping through connected successors, `Flow` manages complex multi-step workflows while keeping individual nodes modular and decoupled. With flows, you can effortlessly combine, nest, and execute entire application pipelines as if they were a single step.

---

# Chapter: BatchFlow

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build resilient single steps (`Node`), process collections within a node (`BatchNode`), and orchestrate multiple connected nodes together into a cohesive sequence (`Flow`). 

However, what happens when you want to execute an entire multi-step *Flow* repeatedly over a collection of different inputs or parameters? Writing manual loops to re-initialize and run a workflow for every single item can quickly become messy and repetitive. In this chapter, we will explore **`BatchFlow`**, a specialized `Flow` subclass designed to loop through a set of parameters and orchestrate a child flow iteratively for each batch item.

---

## What is a `BatchFlow`?

While a standard `Node` processes a list of items sequentially inside a single step, a `BatchFlow` takes a list of parameter dictionaries and executes a whole sub-workflow for each dictionary. 

Let's look at how it is implemented in the source code:

```python
class Flow(BaseNode):
    # ... Flow implementation (start, get_next_node, _orch, etc.) ...
    pass

class BatchFlow(Flow):
    def _run(self,shared):
        pr=self.prep(shared) or []
        for bp in pr: self._orch(shared,{**self.params,**bp})
        return self.post(shared,pr,None)
```

### Breaking Down the Code

1. **Inheriting from `Flow`**: Because `BatchFlow` inherits from `Flow`, it retains all the capabilities of a normal flow—such as defining a starting node, tracking successors, and running an orchestration loop (`_orch`).
2. **The `_run` Method Override**: 
   - `pr = self.prep(shared) or []`: The `BatchFlow` begins by calling its `prep` method to fetch a collection of parameter dictionaries from the `shared` state. If it returns `None`, it defaults to an empty list.
   - **The Iteration Loop**: `for bp in pr: self._orch(shared, {**self.params, **bp})`. For every item (`bp`) in the prepared batch list, it triggers the flow's orchestration engine (`_orch`). It merges any base parameters (`self.params`) with the specific batch parameters (`bp`), giving each iteration its own isolated configuration.
   - **`self.post`**: Finally, it calls the `post` method to clean up or summarize the batch run.

---

## Why is it Designed This Way?

In workflow automation and data processing pipelines, it is very common to want to apply the *same* multi-step process (e.g., "download data -> parse -> save") across *different* independent targets (e.g., multiple user IDs, multiple file paths, or multiple configuration profiles).

Instead of forcing you to write boilerplate loops inside your node logic, `BatchFlow` elevates iteration to the **architectural level**. It cleanly separates:
* **What** data or parameters need to be processed (handled by `prep`).
* **How** the multi-step workflow processes each item (handled by the child flow nodes).

---

## Summary

In this chapter, we explored **`BatchFlow`**, a powerful subclass of `Flow` that automates running an entire multi-step workflow over a collection of parameters. By implementing a custom `_run` method that loops through prepared batch items and passes merged configurations into the orchestration engine, `BatchFlow` allows developers to cleanly scale complex sub-workflows across multiple inputs with minimal boilerplate code.

---

# Chapter: AsyncNode

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build resilient single steps (`Node`), process collections (`BatchNode`), and orchestrate complex multi-step workflows (`Flow` and `BatchFlow`). 

So far, all our nodes have executed synchronously—blocking the thread while waiting for files to read, databases to respond, or API calls to return. But modern Python applications thrive on concurrency, especially when dealing with I/O-bound operations. In this chapter, we will explore **`AsyncNode`**, an asynchronous counterpart to `Node` that provides non-blocking execution hooks and async retry capabilities.

---

## Why Do We Need `AsyncNode`?

Standard `Node` instances rely on synchronous methods like `time.sleep()` for waiting out retries and blocking function calls for execution. If your node makes an HTTP request, the entire thread pauses until the response arrives. 

`AsyncNode` solves this by introducing asynchronous equivalents for every lifecycle hook:
*   `prep_async(shared)` instead of `prep(shared)`
*   `exec_async(prep_res)` instead of `exec(prep_res)`
*   `exec_fallback_async(prep_res, exc)` instead of `exec_fallback(prep_res, exc)`
*   `post_async(shared, prep_res, exec_res)` instead of `post(shared, prep_res, exec_res)`

By leveraging Python's `asyncio` framework, `AsyncNode` lets your workflows yield control during waiting periods, freeing up the event loop to run other tasks concurrently.

---

## Exploring the Source Code

Let's look at how `AsyncNode` is defined in PocketFlow:

```python
class AsyncNode(Node):
    async def prep_async(self, shared): pass
    async def exec_async(self, prep_res): pass
    async def exec_fallback_async(self, prep_res, exc): raise exc
    async def post_async(self, shared, prep_res, exec_res): pass
    
    async def _exec(self, prep_res): 
        for self.cur_retry in range(self.max_retries):
            try: return await self.exec_async(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1: return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0: await asyncio.sleep(self.wait)
                
    async def run_async(self, shared): 
        if self.successors: warnings.warn("Node won't run successors. Use AsyncFlow.")  
        return await self._run_async(shared)
        
    async def _run_async(self, shared): 
        p = await self.prep_async(shared)
        e = await self._exec(p)
        return await self.post_async(shared, p, e)
        
    def _run(self, shared): raise RuntimeError("Use run_async.")
```

### Key Design Highlights:

1. **Inheritance from `Node`**: `AsyncNode` inherits the retry configuration parameters (`max_retries` and `wait`) from regular `Node` objects, maintaining a familiar API.
2. **Non-Blocking Retries**: Inside `_exec`, when an exception occurs, it uses `await asyncio.sleep(self.wait)` instead of freezing the thread with `time.sleep()`.
3. **Async Lifecycle Execution**: `_run_async` coordinates the asynchronous pipeline: it awaits preparation (`prep_async`), executes with retry logic (`_exec`), and finalizes with post-processing (`post_async`).
4. **Safety Guardrails**: Notice the synchronous `_run` method at the bottom—it explicitly raises a `RuntimeError("Use run_async.")`. This prevents accidental blocking execution of an asynchronous node.

---

## Building Concurrent Variants

PocketFlow also extends `AsyncNode` into batch and parallel structures so you can process multiple items concurrently using `asyncio.gather`:

```python
class AsyncBatchNode(AsyncNode, BatchNode):
    async def _exec(self, items): return [await super(AsyncBatchNode,self)._exec(i) for i in items]

class AsyncParallelBatchNode(AsyncNode, BatchNode):
    async def _exec(self, items): return await asyncio.gather(*(super(AsyncParallelBatchNode,self)._exec(i) for i in items))
```

*   **`AsyncBatchNode`** loops through items sequentially using `await` for each step.
*   **`AsyncParallelBatchNode`** fires off all items simultaneously using `asyncio.gather`, dramatically speeding up independent I/O operations like bulk API requests.

---

## Chapter Summary

In this chapter, we introduced **`AsyncNode`**, PocketFlow's solution for non-blocking, asynchronous workflow steps. By providing asynchronous lifecycle hooks (`prep_async`, `exec_async`, `post_async`) and non-blocking retry mechanisms powered by `asyncio.sleep`, `AsyncNode` allows applications to handle high-concurrency workloads seamlessly. Coupled with `AsyncBatchNode` and `AsyncParallelBatchNode`, developers gain fine-grained control over how collections of tasks are executed concurrently, setting the stage for fully asynchronous flow orchestration.

---

# Chapter: AsyncBatchNode and AsyncParallelBatchNode

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build asynchronous single steps using `AsyncNode` to handle I/O-bound tasks without blocking our application. We also saw how `BatchNode` allows synchronous nodes to process collections of items out of the box.

However, what happens when you combine asynchronous execution with batch processing? When dealing with a list of items—such as fetching multiple URLs or processing a batch of asynchronous API requests—you often want to process those items either **sequentially** one after another, or **concurrently** all at once using `asyncio.gather`. 

In this chapter, we will explore **`AsyncBatchNode`** and **`AsyncParallelBatchNode`**, advanced asynchronous nodes designed to handle batch items efficiently.

---

## The Need for Async Batch Nodes

When processing collections asynchronously, two common patterns emerge:
1. **Sequential processing:** You want to run async operations on a list of items one by one (perhaps to respect rate limits or maintain strict order).
2. **Parallel processing:** You want to fire off all async operations simultaneously to maximize speed and minimize total waiting time.

PocketFlow provides dedicated classes for both patterns by combining `AsyncNode` with `BatchNode`.

---

## 1. `AsyncBatchNode` (Sequential Execution)

`AsyncBatchNode` inherits from both `AsyncNode` and `BatchNode`. It takes a list of items and processes them **sequentially** using an asynchronous loop.

### Source Code Breakdown

```python
class AsyncBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return [await super(AsyncBatchNode,self)._exec(i) for i in items]
```

### How It Works
* **Inheritance:** It inherits asynchronous capabilities from `AsyncNode` and batch handling structure from `BatchNode`.
* **Sequential Loop:** The `_exec` method iterates over each item in `items`. 
* **`await` per item:** For each item, it calls `super()._exec(i)` (which leverages `AsyncNode`'s retry and execution logic) and `await`s it before moving on to the next item.

---

## 2. `AsyncParallelBatchNode` (Concurrent Execution)

`AsyncParallelBatchNode` also inherits from `AsyncNode` and `BatchNode`, but instead of running items one by one, it runs them **all concurrently** using Python's `asyncio.gather`.

### Source Code Breakdown

```python
class AsyncParallelBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return await asyncio.gather(*(super(AsyncParallelBatchNode,self)._exec(i) for i in items))
```

### How It Works
* **Generator Expression:** It generates a sequence of asynchronous execution tasks for every item in the batch.
* **`asyncio.gather`:** It wraps these tasks in `asyncio.gather(...)`, which schedules them to run concurrently on the event loop.
* **Performance Boost:** Instead of waiting for item 1 to finish before starting item 2, all items are processed simultaneously, drastically reducing the total execution time for I/O-bound operations.

---

## Practical Example

Here is how you might use an `AsyncParallelBatchNode` to fetch data for multiple user IDs concurrently:

```python
import asyncio
from pocketflow import AsyncParallelBatchNode

class FetchUserDataNode(AsyncParallelBatchNode):
    async def exec_async(self, user_id):
        # Simulate a network request
        print(f"Fetching user {user_id}...")
        await asyncio.sleep(1)
        return {"user_id": user_id, "status": "active"}

# Usage
async def main():
    node = FetchUserDataNode()
    # A batch of user IDs to process concurrently
    user_ids = [101, 102, 103, 104]
    
    # Run the node asynchronously with the batch
    results = await node.run_async(user_ids)
    print("Results:", results)

# asyncio.run(main())
```

In this example, all four user requests fire off at the same time. Rather than taking 4 seconds sequentially, the entire batch finishes in roughly 1 second.

---

## Summary

In this chapter, we explored **`AsyncBatchNode`** and **`AsyncParallelBatchNode`**, two specialized classes that bridge the gap between collections and asynchronous execution. While `AsyncBatchNode` processes batch items sequentially using a loop, `AsyncParallelBatchNode` leverages `asyncio.gather` to execute all items concurrently. By choosing the right node for your workflow, you can easily balance between rate-limiting sequential tasks and maximizing performance with parallel execution.

---

# Chapter: AsyncFlow

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build asynchronous single steps (`AsyncNode`), process batches of items concurrently (`AsyncParallelBatchNode`), and orchestrate synchronous steps into workflows (`Flow`). 

However, real-world applications often require a hybrid approach. You might have a workflow containing a mix of synchronous steps (like a CPU-heavy data parsing function) and asynchronous steps (like an async API call to an LLM or database). How do you coordinate both types of nodes smoothly inside an event loop without breaking your orchestration?

In this chapter, we will explore **`AsyncFlow`**, an asynchronous orchestrator designed to coordinate both synchronous and asynchronous nodes within an event loop.

---

## What is an `AsyncFlow`?

`AsyncFlow` inherits from both `Flow` and `AsyncNode`. This dual heritage gives it superpowers: it can act as a standard asynchronous node (meaning it can be awaited and run inside an event loop via `run_async`), while internally managing a start node and executing an orchestration loop (`_orch_async`).

Let's look at how `AsyncFlow` is implemented in the source code:

```python
class AsyncFlow(Flow,AsyncNode):
    async def _orch_async(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: 
            curr.set_params(p)
            last_action = await curr._run_async(shared) if isinstance(curr,AsyncNode) else curr._run(shared)
            curr = copy.copy(self.get_next_node(curr,last_action))
        return last_action
    async def _run_async(self,shared): 
        p = await self.prep_async(shared)
        o = await self._orch_async(shared)
        return await self.post_async(shared,p,o)
    async def post_async(self,shared,prep_res,exec_res): return exec_res
```

### Understanding the Orchestration Logic

The heart of `AsyncFlow` is the `_orch_async` method. Let's break down why it is designed this way:

1. **Mixed-Node Compatibility**: Inside the `while curr:` loop, the orchestrator checks the type of the current node:
   ```python
   last_action = await curr._run_async(shared) if isinstance(curr,AsyncNode) else curr._run(shared)
   ```
   If the current step is an instance of `AsyncNode`, it awaits its asynchronous execution (`_run_async`). If it is a standard, synchronous node, it executes it synchronously (`_run`). This allows you to seamlessly mix legacy or CPU-bound synchronous code with modern async I/O code inside the same workflow.
2. **Dynamic Routing**: Just like regular flows, it uses `self.get_next_node(curr, last_action)` to determine the next step based on the action returned by the current node.
3. **Parameter Propagation**: It ensures that parameters (`params`) are passed down and updated for each node in the sequence.

---

## Expanding to Batch and Parallel Flows

Just as PocketFlow provides batch variants for standard flows, it also provides asynchronous batch variants built on top of `AsyncFlow`:

```python
class AsyncBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        for bp in pr: await self._orch_async(shared,{**self.params,**bp})
        return await self.post_async(shared,pr,None)

class AsyncParallelBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared): 
        pr=await self.prep_async(shared) or []
        await asyncio.gather(*(self._orch_async(shared,{**self.params,**bp}) for bp in pr))
        return await self.post_async(shared,pr,None)
```

- **`AsyncBatchFlow`** prepares a list of parameter items asynchronously, then executes the entire sub-flow sequentially for each item in the batch.
- **`AsyncParallelBatchFlow`** takes that same list of prepared items and fires off multiple instances of the sub-flow *concurrently* using `asyncio.gather(...)`, maximizing throughput for independent workloads.

---

## Summary

In this chapter, we explored **`AsyncFlow`**, the asynchronous orchestrator that bridges the gap between synchronous and asynchronous code. By inheriting from both `Flow` and `AsyncNode`, `AsyncFlow` enables developers to build flexible event-loop-driven workflows where individual steps can be either synchronous functions or asynchronous coroutines. Coupled with `AsyncBatchFlow` and `AsyncParallelBatchFlow`, it provides a powerful foundation for orchestrating complex, high-performance data pipelines and agentic workflows.

---

# Chapter: AsyncBatchFlow and AsyncParallelBatchFlow

Welcome to the next chapter of the PocketFlow tutorial! In previous chapters, we learned how to build asynchronous workflows (`AsyncFlow`) and how to scale batch processing within individual nodes either sequentially (`AsyncBatchNode`) or concurrently using `asyncio.gather` (`AsyncParallelBatchNode`).

So far, our batch capabilities have been limited to a *single node*. But what happens when you want to execute an entire multi-step asynchronous workflow multiple times over a list of different batch payloads? 

In this chapter, we will explore **`AsyncBatchFlow`** and **`AsyncParallelBatchFlow`**. These high-level asynchronous orchestrators allow you to scale an entire multi-step flow across multiple batch payloads, running them either **sequentially** one-by-one or **in parallel** concurrently.

---

## The Need for Flow-Level Batching

Imagine you are building an AI-powered document processing pipeline. Your workflow consists of multiple steps: reading a document, summarizing it via an API call, and saving the result to a database. You don't just want to run this pipeline for one document; you want to run it for a list of 50 documents simultaneously. 

While you could write your own `for` loop or manual `asyncio.gather` wrapper around an `AsyncFlow`, doing so repeatedly clutters your codebase. `AsyncBatchFlow` and `AsyncParallelBatchFlow` bake this capability right into PocketFlow's architecture.

---

## Meet the Classes

Let's examine how these two orchestrators are implemented in PocketFlow:

```python
class AsyncBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        for bp in pr: await self._orch_async(shared,{**self.params,**bp})
        return await self.post_async(shared,pr,None)

class AsyncParallelBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared): 
        pr=await self.prep_async(shared) or []
        await asyncio.gather(*(self._orch_async(shared,{**self.params,**bp}) for bp in pr))
        return await self.post_async(shared,pr,None)
```

### 1. `AsyncBatchFlow` (Sequential Execution)
* **What it does:** It prepares a list of batch payloads (`pr`) asynchronously, then loops through each payload (`bp`) one after another. For each payload, it runs the underlying workflow using `_orch_async`.
* **Why it's designed this way:** Sequential execution is ideal when your batch payloads share a limited resource (like a rate-limited API or a database connection pool) where sending hundreds of requests at the exact same millisecond would trigger errors or blocks.

### 2. `AsyncParallelBatchFlow` (Concurrent Execution)
* **What it does:** It gathers the list of batch payloads and fires off all workflow executions concurrently using `asyncio.gather(*(self._orch_async(...) for bp in pr))`.
* **Why it's designed this way:** When your tasks are independent network-bound operations (such as fetching data from independent URLs or calling an LLM API with high concurrency limits), running them in parallel drastically reduces total execution time.

---

## How to Use Them

Using an asynchronous batch flow follows the familiar PocketFlow pattern. You define your nodes, link them into an `AsyncFlow`, and then wrap or use them with the batch orchestrator.

Here is a conceptual example of setting up a parallel batch flow:

```python
import asyncio
from pocketflow import AsyncFlow, AsyncParallelBatchFlow, AsyncNode

# 1. Define asynchronous steps
class FetchDataNode(AsyncNode):
    async def prep_async(self, shared):
        # The batch payload is passed via self.params
        return self.params.get("url")
    async def exec_async(self, url):
        # Simulate async network request
        await asyncio.sleep(1)
        return f"Data from {url}"
    async def post_async(self, shared, prep_res, exec_res):
        shared["last_fetched"] = exec_res

# 2. Build the flow
fetch_node = FetchDataNode()
my_workflow = AsyncFlow(start=fetch_node)

# 3. Create a parallel batch wrapper around the flow
class MyBatchWorkflow(AsyncParallelBatchFlow):
    async def prep_async(self, shared):
        # Provide a list of batch payloads
        return [{"url": "api.site.com/1"}, {"url": "api.site.com/2"}, {"url": "api.site.com/3"}]

# 4. Run it asynchronously
async def main():
    shared_state = {}
    batch_flow = MyBatchWorkflow(start=fetch_node)
    await batch_flow.run_async(shared_state)

asyncio.run(main())
```

In this example, instead of running `api.site.com/1`, waiting for it to finish, and moving to the next, `AsyncParallelBatchFlow` executes all three URL requests concurrently, cutting the total wait time down from 3 seconds to roughly 1 second.

---

## Chapter Summary

In this chapter, we explored **`AsyncBatchFlow`** and **`AsyncParallelBatchFlow`**, PocketFlow's high-level orchestrators designed to scale entire multi-step asynchronous workflows across collections of batch payloads. We learned that `AsyncBatchFlow` processes payloads sequentially to respect rate limits or shared resources, while `AsyncParallelBatchFlow` leverages `asyncio.gather` to execute multiple workflow instances concurrently for maximum throughput. With these tools, you can seamlessly scale complex, I/O-bound pipelines to handle bulk data with ease.