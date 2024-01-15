# HyperConfig

[![Build Status](https://travis-ci.org/your-username/hyperconfig.svg?branch=main)](https://travis-ci.org/rchindris/hyperconfig)
[![PyPI version](https://badge.fury.io/py/hyperconfig.svg)](https://badge.fury.io/py/hyperconfig)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

HyperConfig is a Python library for creating schema-based configuration. 
It allows zero code configuration definition where both the structure and the 
configuration values are validated using YAML based schema definition files.


Advantages:

- less code: define the structure in YAML, validate and load configs using a one-liner.
- shared schemas: define once, use in multiple projects.
- extensibility: add configuration types and validation rules without coding.

## Installation

```bash
pip install hyperconfig

```

## Usage

Define your schema in a definition file, `ships.yaml`:

``` yaml
# Spaceship Configuration Schema

ship_type:
  type: str
  validator: hval.isalpha()
  required: true

shipcolor:
  type: str
  validator: hval.lower() in ['red', 'blue', 'green', 'yellow', 'gray']
  required: true

enginepower:
  type: int
  validator: 100 <= hval <= 1000
  required: true

shieldlevel:
  type: float
  validator:  0.0 <= hval <= 1.0
  required: true

ship:
  captain: str
  crew:
   type: int
   validator: hval > 0
  class: shiptype
  color: shipcolor
  shields: shieldlevel
  engines: enginepower
```

Then use the schema to create configuration values, `gameconfig.yaml`:

``` yaml
use: ships

ncc1701=ship:
  captain: James T. Kirk
  crew: 203
  class: constitution
  color: gray
  shields: 1.0
  engines: 900
```

and load it:

``` python
>>> from hyperconfig import HyperConf
>>> config = HyperConf.load("gameconfig.yaml")
>>> print(config.ncc1701.captain)
```

Please check the documentation at https://hyperconf.readthedocs.io/en/latest/index.html

## License

This project is licensed under the MIT License - see the LICENSE file for details.

