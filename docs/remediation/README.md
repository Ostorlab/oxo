---
sidebarDepth: 2
---

# Remediation

Ostorlab provides remediation capabilities to ensure vulnerabilities are fixed urgently, diligently and efficiently.
These capabilities are managed through a ticketing system that aggregates and pairs all vulnerabilities with a ticket.

The remediation system can either be used as a standalone system, or seamlessly integrate with 3rd party ticketing systems
like Jira.

The remediation system offers the following capabilities:

* automatically manage the lifecycle of a vulnerability to ensure fixes are verified and enable tracking of their progress
* provide ticket management capabilities to set priorities, assign an owner and update statuses
* collaborate with team members within the same organisation or by inviting users to your organisation
* set policies to ensure fixes are applied timely and detect missed fixed for tracking and escalations
* collect metrics on the health of your security program and enable data backed strategic decision

## Ticket Lifecycle

Ostorlab automates the lifecycle of tickets linked to detected vulnerabilities. The ticket lifecycle provides the
following capabilities and guarantees:

* A ticket is automatically created in the case of a newly detected vulnerability. The ticket details will contain 
information about the vulnerability. Priorities are set automatically based on the vulnerability severity.

![Ticket Detail](/remediation/ticket_detail.png)

* The platform will aggregate future occurrences of the same vulnerability in the same ticket. Aggregation is done either
by ticket detail, for instance all SQL injection will have a single ticket, or by an internal attribute called DNA
that uniquely identify each vulnerability. The DNA is computed based on the type of vulnerability to ensure it is uniquely
identified.

![Vulnerability Aggregation](/remediation/vuln_aggregate.png)

* Tickets can be marked as fixed. For fixed tickets,

![Fixed Ticket](/remediation/ticket_fixed.png)

the platform will automatically mark the ticket as verified if the vulnerabilities are indeed absent from future scans

![Verified Ticket](/remediation/ticket_verified.png)

or will re-open the same ticket.

![Reopened Ticket](/remediation/ticket_reopen.png)

* Tickets can be marked as an exception or a false-positive. Excepted and false-positive tickets are kept as is when new occurrences
of the same vulnerability are found.

![Exception Ticket](/remediation/ticket_exception.png)

Manually created tickets also benefit from the same ticket management capabilities if a vulnerability is assigned
to the ticket.

## Ticket Management

A ticket has multiple settings to reflect urgency, priority, ownership or ease searching and filtering.

All edits to ticket are tracked in the activity section to see who did what and when.

![Ticket Activity](/remediation/ticket_activity.png)

### Urgency and Priority

The ticket has a priority setting from P0 to P3. P0 is the most urgent to P3 the least urgent.

![Ticket Priority](/remediation/update_priority.png)

### Ownership

Manually created ticket will have a reporter. Tickets can be assigned an owner who typically ensure the vulnerabilities
are fixed.

Tickets can be assigned to an existing user, who can access the ticket, provided he is part of the organisation owning the ticket.
Otherwise he will receive an invitation to join the organisation.

![Ticket Priority](/remediation/assign_user.png)

Invitation can only be approved by an ADMIN of the organisation, which can be done at the Organisation / Invitation section.

![Invitations](/remediation/invitations.png)

Once the user creates an account and has his invitation approved, he will be automatically assigned the tickets.

### Tags

Tickets can have multiple tags assigned. A tag have both a name and a value. Separation of tag name and values are to
enable add extra meaning to the ticket. Like for instance adding an `env` tag with values like `prod`, `qa` and `test`, or adding
`workstream` tag with values like `featureXYZ`.

Setting the value is not obligatory as names only are acceptable

![Tags](/remediation/tags.png)

### Searching

The remediation sections offers multiple search capabilities. Searching is done by specifying a supported keyword
mapped with the search value.

Supported keywords are:

* __priority__: search by priority, values are P0 to P3
* __status__: search by ticked status, values are OPEN, REOPEN, FIXED, FIXED_VERIFIED, EXCEPTION, FALSE_POSITIVE
* __assignedEmail__: search by assigned email address
* __reporterEmail__: search by reporter email address
* __toMe__ (boolean): shortcut to find tickets assigned to me, values are true and false 
* __byMe__ (boolean): shortcut to find ticket reported by me, values are true and false
* __tagName__: search by tag name
* __tagValue__: search by tag value

![Ticket Search](/remediation/ticket_search.png)


## Collaboration

The remediation offers organisation-wide collaboration. Everything within an organisation is accessible and visible to
all members within the same organisation.

This includes scan access, vulnerability data access, ticket data access, etc.

Collaboration on tickets can be done using the comment section, comments can be updated or deleted. A trace of the
action is however recorded in the activity section.

![Comments](/remediation/comments.png)

In the case some data can't be shared across multiple teams, dedicated organisations can be created to confine all interactions
within the same organisation. This typically applies when for instance an application is built by an external 3rd party,
while others are built internally.

![Create Organisation](/remediation/organisation_create.png)

![Invite Users](/remediation/invite_users.png)

## Policies

One of the 5 pillars of autonomous security is Policies. There are several policy types, like:

* __Patching policy__ to define when vulnerabilities of different severity are fixed
* __Freshness policy__ to define how outdated are old can be of software of hardware be running on production
* __Enforcement policy__ to define under what conditions can a dangerous system be quarantined or disconnected

These are just sample of remediation policies. At this stage Ostorlab only supports setting and enforcing the patching
policy.

![Patching Policy](/remediation/policy.png)

### Patching Policy

Patching policy defines SLO (Service Level Objectives) to handle confirmed vulnerabilities and hardening recommendations.
An example would be fixing a high severity issue within 5 days.

The policy is enforced by the ticketing system that compares ticket creation time with the highest vulnerability severity
against defined policy.

![Ticket List](/remediation/ticket_list.png)

![Ticket Calendar SLO](/remediation/ticket_calendar_slo.png)


## Metrics and Dashboards

While ticketing helps managing the daily routines and ensuring things are fixed and not dropped, they are not sufficient
to have a holistic look at how a security program is performing.

For this reason the ticketing system is complemented with a metrics and dashboard pillar, the 5th pillar  of autonomous security programs.

The metrics module collects several metrics that are either time based, like count of high severity issues, count of fixed
issues and global metrics, like re-open rate, % of secure assets, etc.

These metrics are accessible in an organisation dashboards that have 5 sections:

### Application Summary

![Application Summary](/remediation/application_summary.png)

Application summary simply lists the most recent assets and their most recent scan status. This allows a quick look into
what has been running and their risk posture.

### Maturity Radar

![Security Posture](/remediation/radare.png)

The radar shows the global metrics that scores on a scale from 0 to 5. The scores are scales to be comparable with
2 anchor values. The first is an organisation average collected across all organisation on the platform. 
The second is a recommended best practice.

The goal is to give a sense to the metrics instead of simply having non-interpretable values.

### Vulnerability and Ticket Trending

![Vulnrability Trending](/remediation/vuln_trending.png)

The trending bars shows count of vulnerability counts and ticket updates focusing on confirmed findings and fixed
and exception status.

The trending bar is configurable to show any period.

![Time Range](/remediation/range.png)

### Scan Heatmap

![Scan Heatmap](/remediation/heatmap.png)

Scan heatmap shows a distribution of scans. This is helpful to ensure that scans are performed on a regular basis, for
instance to ensure that there is at least a weekly coverage.

### Ticket Calendar

![Calendar](/remediation/calendar.png)

The ticket calendar shows all open and reopen tickets by time. Fixed, exception and false positive tickets are not shown
as they should not trigger any action.

