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

The file defines some third-party data connections and DAG-workflow stores for our tasks. We have two connections here: one names `rdb-conn`, connecting to the postgresql database `yourdb` with driver `rdb`, the other names `elastic-conn`, is a document database based by a elasticsearch server.

In the dagstore section, we use the famous job scheduler of LinkedIn, [Azkaban](https://azkaban.github.io/), to schedule our data workflow. You may already find that `Parade` can be easily integrated with other third-party components with different **drivers**. This is benefited from its easy & unified plugin based architecture, which we'll present later.

The layout of example workspace so far are:
- Core package holds our data tasks and some contributed components
- The top level contains configuration files

`Parade` expects you keeps your workspace nice and tidy. There's a place for everything, and everything is in its place.

### Compose Tasks
In this tutorial, we will load the [IMDB 5000 Movie Dataset](https://www.kaggle.com/deepmatrix/imdb-5000-movie-dataset) published on [Kaggle](https://www.kaggle.com/) into our database, and process some further analysis on this dataset, then re-store the analysis result into another table. After that we try to build a DAG workflow with these tasks and schedule them as a whole.

#### Compose a ETL task
For sake of convenience, we've placed the dataset as a unzipped CSV file in our github repo, check it [here](https://raw.githubusercontent.com/bailaohe/parade/master/assets/movie_metadata.csv). In the first task, we will load this dataset as a table into our postgresql/mysql database.

Use `gentask` subcommand of `Parade` to generate the skeleton for this ETL task.

```bash
> parade gentask movie_data -t etl
```

Open the skeleton python file `example/task/movie_data.py`, you'll find lots of attributes as `@property` functions you can override to customize the task. We only reserve the required attributes to make the source tidy:

```python
# -*- coding:utf-8 -*-
from parade.core.task import ETLTask


class MovieData(ETLTask):

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        raise NotImplementedError("The target is required")

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        raise NotImplementedError
```

The first `@property` function `target_conn` is used to specify the connection where we store our ETL data. We can simply set it to the connection key in our configuration, like `rdb-conn`.

The other function `execute_internal` is the core logic of this task. We simply load the raw csv dataset, do some projection & filter operation on it, and then store the result. `Parade` can handle `Pandas` Dataframe (and dict) by default. So we can use pandas to process the data and return the result dataframe directly. The edited task is:

```python
# -*- coding:utf-8 -*-
from parade.core.task import ETLTask


class MovieData(ETLTask):

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'rdb-conn'

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        df = pd.read_csv('https://raw.githubusercontent.com/bailaohe/parade/master/assets/movie_metadata.csv')

        # Process projection on the dataset to get our interested attributes
        df = df[['movie_title', 'genres', 'title_year', 'content_rating', 'budget', 'num_voted_users', 'imdb_score']]

        # Filter out records with *NAN* title_year and budget
        df = df[pd.notnull(df['title_year'])]
        df = df[df['budget'] > 0]
        
        # Extract the genres ROOT
        df['genres_root'] = df['genres'].apply(lambda g: g.split('|')[0])

        return df
```

#### Execute the ETL task

Use the following `Parade` command to execute the single task `movie_data`.

```bash
> parade exec movie_data
2017-05-24 16:37:14,913 program_name DEBUG [11758] [exec.py:20]: prepare to execute tasks ['movie_data']
2017-05-24 16:37:14,914 program_name INFO [11758] [exec.py:27]: single task movie_data provided, ignore its dependencies
2017-05-24 16:37:35,634 program_name WARNING [11758] [rdb.py:72]: Detect columns with float types ['title_year', 'budget', 'imdb_score'], you better check if this is caused by NAN-integer column issue of pandas!
2017-05-24 16:37:35,636 program_name WARNING [11758] [rdb.py:80]: Detect columns with object types ['movie_title', 'genres', 'content_rating', 'genres_root'], which is automatically converted to *VARCHAR(256)*, you can override this by specifying type hints!
2017-05-24 16:37:38,374 program_name INFO [11758] [rdb.py:105]: Write to movie_data: rows #0-#10000
```

When the execution is done, you can check your newly loaded data in the databased labeled by `rdb-conn`.

```sql
> select count(1) from movie_data;
+----------+
| count(1) |
+----------+
|     4543 |
+----------+
1 row in set (0.01 sec)
```

Relexed and comfortable, right? However, when you check the generated table, you may find something unsatisfactory.

```sql
> show create table movie_data;

CREATE TABLE `movie_data` (
  `movie_title` varchar(256) DEFAULT NULL,
  `genres` varchar(256) DEFAULT NULL,
  `title_year` double DEFAULT NULL,
  `content_rating` varchar(256) DEFAULT NULL,
  `budget` double DEFAULT NULL,
  `num_voted_users` bigint(20) DEFAULT NULL,
  `imdb_score` double DEFAULT NULL,
  `genres_root` varchar(256) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8

1 row in set (0.00 sec)
```

The columns `title_year` and `budget` should be of type Integer in original dataset, but stored as Double in the target table. This is because both of them has **NAN** value in the raw dataset. Although we've filtered NAN-value records out, `Pandas` automatically convert Integer columns with NAN-value into float. Check the outputs of execution above, `Parade` has warned on this issue. Moreover, all String-typed columns have been converted into VARCHAR(256) indistinctively.

To address this issue, we further customize the datatype of ETL target with `@property` function `target_typehints`. `Parade` provides a compact set of basic datatypes. We simply return a column-name to `Parade`-datatype dict in the function. 

We can further customize the indexes on the ETL target with `@property` function `target_indexes`. The `rdb` connection driver can recognize this attribute and build indexes after writing the result. The final task source is as follows:

```python
# -*- coding:utf-8 -*-

from parade.core.task import ETLTask
from parade.type import stdtypes
import pandas as pd


class MovieData(ETLTask):

    @property
    def target_conn(self):
        """
        the target connection to write the result
        :return:
        """
        return 'stat'

    @property
    def target_typehints(self):
        """
        a dict of column_name => datatype, to customize the data type before write target
        :return:
        """
        return {
            'movie_title': stdtypes.StringType(128),
            'genres': stdtypes.StringType(128),
            'genres_root': stdtypes.StringType(32),
            'content_rating': stdtypes.StringType(16),
            'title_year': stdtypes.IntegerType(),
            'budget': stdtypes.IntegerType(20),
        }

    @property
    def target_indexes(self):
        """
        a string or a string-tuple or a string/string-tuple list to specify the indexes on the target table
        :return:
        """
        return ['movie_title', ('title_year', 'genres')]

    def execute_internal(self, context, **kwargs):
        """
        the internal execution process to be implemented
        :param context:
        :param kwargs:
        :return:
        """
        df = pd.read_csv('https://raw.githubusercontent.com/bailaohe/parade/master/assets/movie_metadata.csv')

        # Process projection on the dataset to get our interested attributes
        df = df[['movie_title', 'genres', 'title_year', 'content_rating', 'budget', 'num_voted_users', 'imdb_score']]

        # Filter out records with *NAN* title_year and budget
        df = df[pd.notnull(df['title_year'])]
        df = df[df['budget'] > 0]
        
        # Extract the genres ROOT
        df['genres_root'] = df['genres'].apply(lambda g: g.split('|')[0])

        return df
```

Re-execute the task and check your database again:

```sql
mysql> show create table movie_data;

CREATE TABLE `movie_data` (
  `movie_title` varchar(128) DEFAULT NULL,
  `genres` varchar(128) DEFAULT NULL,
  `title_year` int(11) DEFAULT NULL,
  `content_rating` varchar(16) DEFAULT NULL,
  `budget` bigint(20) DEFAULT NULL,
  `num_voted_users` bigint(20) DEFAULT NULL,
  `imdb_score` double DEFAULT NULL,
  `genres_root` varchar(32) DEFAULT NULL,
  KEY `idx_movie_title` (`movie_title`),
  KEY `idx_title_year_genres` (`title_year`,`genres`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8

1 row in set (0.02 sec)
```

#### Compose another Analysis task

	
 



