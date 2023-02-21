=======
metrico
=======
This is in development! Just a kind of beta version!

Just some metrics for social networks or basically any platform where users post content, write comments and following each other.

First Steps
-----------
It is easy to install::

    pip install metrico

Before you can work with metrico, you have to setup a config file "metrico.toml". The api keys are the most important configuration::

    [hunters.youtube]
    config.key = "AIza..."

Now we setup the database::

    metrico tools setup

Add a account to the database::

    metrico add DistroTube

Time to go data hunting. There for are a lot of options, but for the beginning we will get all the medias from all accounts::

    metrico hunt accounts

This can take a while. Next let's see what we get::

    metrico hunt show medias --limit 5


Some commands::

    metrico --help
    metrico tools config
    metrico tools hunter
    metrico tools migrate
    metrico add youtube account "DistroTube"
    metrico hunt accounts


Run local PostgresSQL with docker::

    docker run --name postgres-metrico -e POSTGRES_USER=metrico -e POSTGRES_PASSWORD=1234 -p 5432:5432 -d postgres

Show container::

    docker ps -a

Stop and delete container::

    docker stop postgres-metrico
    docker rm postgres-metrico

