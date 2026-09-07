# 3. Use CODEOWNERS Github feature to restrict approved reviewers

## Status

Accepted

## Context

As dodal expands and covers an increasing number of beamlines it is important to maintain quality. So far we have seen good results from following bluesky's own standards: Encouraging high test coverage, readable code (including type annotations, where appropriate) and collective ownership, including via thorough reviews which appropriately balance velocity with technical debt management. We would like to make sure this developer culture is preserved as we expand.

## Decision

Have a team of approved reviewers in the DiamondLightSource Github organisation. Every PR into dodal **must** be reviewed by a member of this team before merging (enforced by repo settings and [CODEOWNERS feature](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)). Have a set of [documented criteria](../reviews.md) for becoming part of the team, with the expectation that any team that regularly works on dodal will become members over time. The hope is that a consistent set of standards can be maintained by the approver community.

## Consequences

PRs will not be mergable until an approved owner has reviewed them, approved individuals/teams will have to review/support onboarding of new individuals/teams for some time before they are approved for review. 

Once a critical mass of Diamond staff are used to this way of working, this ADR may be obsolete and should be replaced with a more open review system.
