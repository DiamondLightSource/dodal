# Approved Reviewers

Code reviews are an important tool for ensuring both quality and collective responsibility for the codebase. Dodal PRs *must* be reviewed by a member of [the approved review team](https://github.com/orgs/DiamondLightSource/teams/bluesky-reviewers) before they are merged. 

## Review Standards and Practices

When reviewing you should ensure the code meets the [repository standards](../reference/standards.rst) and [device standards](../reference/device-standards.rst). Approved reviewers will adhere to the following, if they do not, junior reviewers and reviewees should feel empowered to hold them to them.

### Questions and Comments

Questions and requests for clarification are encouraged. If you have comments for the reviewer you could add them with the following prefixes to be helpful:

- Nit - This is arguably just taste, you don't mind if the developer doesn't follow this
- Should - This will improve code quality but unlikely to affect functionality. If the developer doesn't want to do this they should write an explanation.
- Must - This will negatively affect functionality if not implemented.

### The Happy Path

If the review passes then the reviewer should approve the change and either the reviewer or PR author should merge it. 

### Requesting Changes

If the review fails the reviewer should request any changes (this issue is said to require rework)
A developer should ideally pick up any rework PRs before starting new work
When a developer is happy that a rework is complete they should press the re-request review button on the PR

### Making Changes

Reviewers should feel free to make small changes to a PR as part of a review e.g. typos, poorly named variables, fixing a test. However, if code has been changed in this way they need then need to run it past another developer (ideally the original developer). This means that no code is merged into main without being looked at by at least 2 people, ensuring collective responsibility for the codebase.
Dismissing a previous reviewer

### Dismissing Stale Reviews

There may be times where one person requests changes on a PR, these changes are addressed and another person then approves it. In this case the PR still cannot be merged until the original review is dismissed. We're happy for people to dismiss stale reviews with the understanding that:

- The new reviewer should check that the must and should comments have been addressed
- If it's a big change it may still be worth the original reviewer looking again, if so they should make this clear to the original reviewer and the person that wrote the code

## Joining the Review Team

At least two members of the review team from two different DLS teams *must* approve adding a new member, neither of them can be on the new member's DLS team. They should ideally both be senior engineers but this will not always be possible. 

### Criteria for New Members

New members should be regular contributors to dodal and should have been "shadow-reviewing" approved reviewers for a period of weeks or months before becoming approved. In both their contributions and reviews they should be consistently demonstrating the following *without prompting*:

- A good understanding of Python, including advanced langauge features such as [generators](https://wiki.python.org/moin/Generators), [coroutines](https://docs.python.org/3/library/asyncio-task.html), [comprehensions](https://www.geeksforgeeks.org/comprehensions-in-python/) and [pattern matching](https://peps.python.org/pep-0636/).
- A pythonic coding style, demonstrated by using appropriate class/variable names, aherence to [PEP 8](https://peps.python.org/pep-0008). 
- Adherence to the review standards above as well as the [repository standards](../reference/standards.rst) and [device standards](../reference/device-standards.rst).
- Indepdant (i.e. not just to satisfy a reviewer) motivation to make sure all code in dodal is well-tested. Use of unit and system tests as appropriate. Clear effort made to keep test coverage high (>90%). 
- Advanced understanding of bluesky and ophyd-async including concepts and best practices, such as how to appropriately split logic between devices/plans/callbacks.

Additionally, they should be regularly raising issues in the repository and demonstrating the ability to write well formed issues, with well defined acceptance criteria, that are understandable without large amounts of context.
