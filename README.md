# Parade

Parade is a simple and out-of-box toolkit to handle data tasks. It can be used for a wide range of purposes, from scheduling ETL tasks to providing web-APIs of data query.

## Requirements

* Python 2.7 or Python 3.3+
* Works on Linux, Windows, Mac OSX, BSD

## Install

The quich way:

```bash
> pip install parade
```

## Basic Usage

After installation, a command line tool *parade* is placed in $PATH. Have a glance at the usage output:

```bash
> parade -h

usage: parade [-h] {init} ...

The CLI of parade engine.

positional arguments:
  {init}
    init      init a workspace to work with

optional arguments:
  -h, --help  show this help message and exit
```

Until now, you can do nothing but to initialize a workspace to place your task and other stuff.

### Initialize Workspace

Type following command to Initialize the workspace named *exmaple*:

```bash
> parade init example
 
New Parade workspace 'example', using template directory 'site-packages/parade/template/workspace', created in:
    /$CMD/example

You can start your first task with:
    cd example
    parade gentask your_task -t etl
```

Enter the workspace directory, and re-check usage again:

```bash
> parade -h
usage: parade [-h] {server,init,sched,gentask,exec} ...

The CLI of parade engine.

positional arguments:
  {server,init,sched,gentask,exec}
    server              start a parade api server
    init                init a workspace to work with
    sched               schedule a flow with a set of tasks
    gentask             generate a task skeleton with specified type
    exec                execute a flow or a set of tasks

optional arguments:
  -h, --help            show this help message and exit
```

You can find much more sub-commands available now. We come to the details of these sub-commands later. At this moment we have a look at the directory structure.

```bash
> tree

.
├── __init__.py
├── example
│   ├── __init__.py
│   ├── contrib
│   │   ├── __init__.py
│   │   ├── connection
│   │   │   └── __init__.py
│   │   └── dagstore
│   │       └── __init__.py
│   └── task
│       └── __init__.py
├── example-default-1.0.yml
└── parade.bootstrap.yml

5 directories, 8 files
```

At top there are a package named *example* (as we specified) and two yaml files. The package has two sub-packages: 

- *contrib* contains user defined components, such as connection drivers, task dagstores, etc.
- *task* holds all the data tasks to execute or schedule.

The yaml file *parade.bootstrap.yml* is just a **pointer** to the configuration repo for this workspace. Its content is as follows:

```
workspace:
  name: example
config:
  name: example
  driver: yaml
  profile: default
  version: 1.0
  uri: "{name}-{profile}-{version}.yml"
```

In this example, we use a local yaml file  *example-default-1.0.yml* as the repo. You can implement your own configuration repo and specify it as `config.driver` in *parade.bootstrap.yml*.


### Compose Task




	
 



