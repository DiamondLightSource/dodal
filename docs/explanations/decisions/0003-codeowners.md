# 3. Use CODEOWNERS Github feature to restrict approved reviewers

## Status

Accepted

## Context

Dodal is a sprawling library that supports a large number of instruments. As it expands, the code quality is naturally likely to decrease due to bloat, duplication, lack of single product ownership and multitudes of stakeholders and use cases understood differently by different people. Members of individual teams are likely to review each other's code based on their own criteria and team pressures, without accounting for the overall quality of the library. We have seen these problems with GDA and wish to avoid a repeat.

## Decision

Have a team of approved reviewers in the DiamondLightSource Github organisation. Every PR into dodal **must** be reviewed by a member of this team before merging (enforced by repo settings and [CODEOWNERS feature](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)). Have a set of [documented criteria](../reviews.md) for becoming part of the team, with the expectation that any team that regularly works on dodal and become members over time. The hope is that a consistent set of standards can be maintained by the approver community.

## Consequences

PRs will not be mergable until an approved owner has reviewed them, approved individuals/teams will have to review/support onboarding of new individuals/teams for some time before they are approved for review. 
