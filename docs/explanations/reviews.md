# Approved Reviewers

Dodal PRs *must* be reviewed by a member of [the approved review team](https://github.com/orgs/DiamondLightSource/teams/bluesky-reviewers) before they are merged. 

## Review Standards

TBD

Then something about juniors should also feel free to point to the guidance on PRs from codeowners and hold them to it

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
