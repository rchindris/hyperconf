# HyperConfig

[![Build Status](https://travis-ci.org/your-username/hyperconfig.svg?branch=main)](https://travis-ci.org/rchindris/hyperconfig)
[![PyPI version](https://badge.fury.io/py/hyperconfig.svg)](https://badge.fury.io/py/hyperconfig)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

HyperConfig is a Python library for schema-based configuration. It allows you to define the structure of the configuraiton files
using a YAML based definition files. It automatically parses and validates your configuration files, enabling:

- less code: define the structure in YAML, validate and load configs using a one-liner.
- shared schemas: define once, use in multiple projects.
- extensibility: add configuration types and validation rules without coding against and API.

## Installation

```bash
pip install hyperconfig

```

## Usage

Define your schema in a definition file, `ships.yaml`:

``` yaml
# Spaceship Configuration Schema

ship_type:
  _type: str
  _validator: hval.isalpha()
  _required: true

ship_color:
  _type: str
  _validator: hval.lower() in ['red', 'blue', 'green', 'yellow', 'gray']
  _required: true

engine_power:
  _type: int
  _validator: 100 <= hval <= 1000
  _required: true

shield_level:
  _type: float
  _validator:  0.0 <= hval <= 1.0
  _required: true

ship:
  captain: str
  crew:
   _type: int
   _validator: hval > 0
  class: ship_type
  color: ship_color
  shields: shield_level
  engines: engine_power
```

Then use the schema to create configuration values, `game_config.yaml`:

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
>>> config = HyperConf.load("game_config.yaml")
>>> print(config.ncc1701.captain)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

HyperConfig was inspired by the need for a flexible and zero-code configuration library.

## Contact

For any questions or feedback, feel free to reach out to radu.chindris@gmail.com

