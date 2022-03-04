[![PyPI version](https://badge.fury.io/py/ostorlab.svg)](https://badge.fury.io/py/ostorlab)
[![Downloads](https://pepy.tech/badge/ostorlab/month)](https://pepy.tech/project/ostorlab)
[![Ostorlab blog](https://img.shields.io/badge/blog-ostorlab%20news-red)](https://blog.ostorlab.co/)
[![Twitter Follow](https://img.shields.io/twitter/follow/ostorlabsec.svg?style=social)](https://twitter.com/ostorlabsec)

# Ostorlab Open-Source Security Scanner

## The Sales Pitch

If this is the first time you are visiting the Ostorlab github page, here is the sales pitch.

A lot of the security testing work is about chaining tools together, taking the output from one file, mangle it, filter
it, prepare it and push it to another tool. Many have tried to have it automated, most have failed.

Ostorlab succeeds where all the rest have failed (shamelessly staring with an air of over-confidence) by simplifying the
hardest part and automated the boring and tedious part.

In layman's term, Ostorlab is:

* Lovely SDK in a lovely langauge (Python). We make the simple cases effortless while supporting the complex one. Either
  it is distributed locking, QPS limiting, multiple instance parallelization, we got you covered.
* A battle tested framework that has been powering Ostorlab Platform for years and used to perform complex dyanmic
  analysis setup and demanding static analysis workloads
* Performant and scalable platform, thanks to the use of message queue, binary and compact message serialisation with
  Protbuf, resilient thanks to docker swarm mode to cite a few
* A store of agents that make is to use and discover tools to add your toolset
* An automated builder for all the open-source supported tools. The moment they release, new version appear on the store
  within minutes
* A GUI to prepare and write down your tool collection setup, no more upper arrow to find that one command.
* Serious focus on documentation, hence this superb sales pitch, a documentation page, multiple tutorials and upcoming
  videos and conference presentations

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

# Publish your first Agent

Check the full tutorial [writing an Ostorlab agent](https://docs.ostorlab.co/tutorials/write-an-ostorlab-agent/)



