# Parade

`Parade` is a simple and out-of-box toolkit to handle data work such as ETL, data analysis, BI reports, etc, and enable fast and flexible integration mechanism with applications. It can be used for a wide range of purposes, from composing & scheduling data workflow to providing unified web-APIs of data query.

## Requirements

* Python 3.3+
* Works on Linux, Windows, Mac OSX, BSD

## Install

The quich way:

```bash
> pip install parade
```

## Basic Usage & Tutorials

After installation, a command line tool *parade* is placed in $PATH. Have a glance at the usage output:

```bash
> parade -h

usage: parade [-h] {search,init} ...

The CLI of parade engine.

positional arguments:
  {search,init}
    search       search a contrib component
    init         init a workspace to work with

optional arguments:
  -h, --help     show this help message and exit
```

Until now, you can do nearly nothing but to initialize a workspace to place your task and other stuff. * We leave the search command later ...

### Initialize Workspace

In this tutorials, we'll compose a series of ETL tasks, compose them into a DAG workflow and schedule the flow with a third-party scheduler (e.g, Azkaban). Type following command to Initialize the workspace named *exmaple*:

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
usage: parade [-h] {gentask,mkdag,search,exec,server,init,install} ...

The CLI of parade engine.

positional arguments:
  {gentask,mkdag,search,exec,server,init,install}
    gentask             generate a task skeleton with specified type
    mkdag               create a dag (flow) with a set of tasks
    search              search a contrib component
    exec                execute a flow or a set of tasks
    server              start a parade api server
    init                init a workspace to work with
    install             install a contrib component into current workspace

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

The first section contains some basic information about the workspace. In the second section, we use a configuration repo based on **default** YAML driver, which is also a yaml file with formatted name `{name}-{profile}-{version}.yml` (You can implement your own configuration repo and specify it as `config.driver` in *parade.bootstrap.yml*). Providing the configuration name, `example`, profile, `default`, and version, `1.0`, the file configuration repo file is *example-default-1.0.yml*.

```
connection:
  # name of the connection
  rdb-conn:
    driver: rdb
    protocol: postgresql
    host: 127.0.0.1
    port: 5432
    user: nameit
    password: changeme
    db: yourdb
    uri: postgresql://nameit:changeme@127.0.0.1:5432/yourdb
  elastic-conn:
    driver: elastic
    protocol: http
    host: 127.0.0.1
    port: 9200
    user: elastic
    password: changeme
    db: example
    uri: http://elastic:changeme@127.0.0.1:9200/
dagstore:
  driver: 'azkaban'
  azkaban:
    host: "http://127.0.0.1:8081"
    username: azkaban
    password: azkaban
    project: TestProject
    notifymail: "yourmail@yourdomain.com"
    cmd: "parade exec {task}"
```

The file defines some third-party data connections and DAG-workflow store for our tasks. We have two connections here: one names `rdb-conn`, connecting to the postgresql database `yourdb` with driver `rdb`, the other names `elastic-conn`, is a document database based by a elasticsearch server.

In the dagstore section, we use the famous job scheduler of LinkedIn, [Azkaban](https://azkaban.github.io/), to schedule our data workflow. You may already find that `Parade` can be easily integrated with other third-party components with different **drivers**. This is benefited from its easy & unified plugin based architecture, which we'll present later.

The layout of example workspace so far are:
- Core package holds our data tasks and some contributed components
- The top level contains configuration files

`Parade` expects you keeps your workspace nice and tidy. There's a place for everything, and everything is in its place.



### Compose Task




	
 



