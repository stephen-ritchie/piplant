# PiPlant
A platform for automated growing of plants.

Originally designed for hydroponics, this system can be used to add
data tracking and automation to any garden system. The basic idea is that
existing devices the system uses (smart plugs, temperature probes, pH sensors, etc.)
can be added and configured within the PiPlant platform. The platform can then be used
as a central location for configuration, data tracking, and automation of these devices.

The first few versions of the platform will be capable of data recording and basic 
automation. However, the goal is for future versions of the platform to respond 
to its own data to improve growing outcomes. Examples of this type of response could be
sending alerts if water temperature moves outside safe bounds, or automatically dosing
solution to maintain safe pH levels.

## Main Features
* Basic automated scheduling for compatible devices. Useful for controlling light
or pump cycles.
* Tracking of air, water, or soil temperatures using DS18B20 sensors.
* Centralized storage and reporting of device data.

### Supported Device List
* TP Link (aka Kasa) smart devices
* DS18B20 temperature probes

## Installation
Python 3 required
```bash
$ git clone https://github.com/stephen-ritchie/piplant.git
$ cd piplant/
$ pip install .
```

## Usage

### Server

```bash
$ cd bin/
$ export FLASK_ENV=production
$ python ./run.py --host <HOST> --port <PORT>
```

### Client
```bash
$ cd piplant/client/
$ export FLASK_ENV=production
$ python ./client.py <SERVER HOSTNAME> <EMAIL> <PASSWORD>
```
