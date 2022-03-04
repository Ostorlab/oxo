[![PyPI version](https://badge.fury.io/py/ostorlab.svg)](https://badge.fury.io/py/ostorlab)
[![Downloads](https://pepy.tech/badge/ostorlab/month)](https://pepy.tech/project/ostorlab)
[![Ostorlab blog](https://img.shields.io/badge/blog-ostorlab%20news-red)](https://blog.ostorlab.co/)
[![Twitter Follow](https://img.shields.io/twitter/follow/ostorlabsec.svg?style=social)](https://twitter.com/ostorlabsec)

# Ostorlab Open-Source Security Scanner

## The Sales Pitch

If this is the first time you are visiting the Ostorlab Github page, here is the sales pitch.

Security testing requires often chaining tools together, taking the output from one, mangling it, filtering it and then
pushing it to another tool. Several tools have tried to make the process less painful, often to end up as yet another
tool to take output from because they only support a certain use-case.

Ostorlab tries to succeed in simplifying the process by simplifying the hardest part and automated the boring and
tedious part while making it its explicit goal to cover all use-cases, from scanning all assets to detecting all
vulnerabilities classes (hopefully).

To do that, Ostorlab focuses on solving:

* Extensibility power
* Developer experience
* Ease of use

To do that, Ostorlab ships with:

* A simple, yet powerful SDK to make simple cases effortless while supporting the complex one, lkie distributed
  locking, QPS limiting, multiple instance parallelization ... 
* A battle tested framework that has been powering Ostorlab Platform for years and used to perform complex dynamic
  analysis setup and demanding static analysis workloads running on multiple machines.
* Performant and scalable design, thanks to the use of message queue with dynamic routing, binary and compact message serialisation with
  protbuf, universal file format using docker image, resilient thanks to docker swarm mode to cite a few
* A store of agents that make is to use and discover tools to add your toolset
* An automated builder for all the open-source supported tools. The moment they release, new version appear on the store
  within minutes
* A GUI to prepare and write down your tool collection setup, no more upper arrow to find that one command.
* Serious focus on documentation, hence this superb sales pitch, a documentation page, multiple tutorials and upcoming
  videos and conference presentations 
* A ready to use one-click template repo to get started.

![Ostorlab Open source](https://blog.ostorlab.co/static/img/ostorlab_open_source/new_scan_run.gif)

Ostorlab is a security scanning platform that enables running complex security scanning tasks involving multiple tools
in an easy, scalable and distributed way.

Ostorlab provides:

* CLI to run scans locally and on Ostorlab's Cloud and access the results.
* SDK to build scanner components called Agents.
* Store to publish Agents and share them with the community.
* Automated Agent builder that takes care of automatically building and releasing Agents directly from the source code
  repo.

# Requirements

For some tasks, like running scans locally, Docker is required. To install docker, please see the following
[instructions](https://docs.docker.com/get-docker/).

# Installing

Ostorlab is shipped as a Python package on Pypi. To install, simply run the following command if you have `pip` already
installed.

```shell
pip install -U ostorlab
```

# Getting Started

To perform your first scan, simply run the following command:

```shell
ostorlab scan run --install --agent agent/ostorlab/nmap --agent agent/ostorlab/tsunami --agent agent/ostorlab/nuclei ip 8.8.8.8
```

This command will download and install the following scanning agents:

* `agent/ostorlab/nmap`
* `agent/ostorlab/tsunami`
* `agent/ostorlab/nuclei`

And will scan the target IP address `8.8.8.8`

To check the scan status:

```shell
ostrlab scan list
```

Once the scan has completed, to access the scan results:

```shell
ostorlab vulnz list --scan-id <scan-id>
ostorlab vulnz describe --vuln-id <vuln-id>
```

# The Store

// TODO

# The Agent Group Builder

// TODO

# Publish your first Agent

// TODO

Check the full tutorial [writing an Ostorlab agent](https://docs.ostorlab.co/tutorials/write-an-ostorlab-agent/)



