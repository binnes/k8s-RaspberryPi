# Local cache for raspberry pi packages

If you are continually rebuilding systems, then you will be continually downloading packages from the web.  You may want to set up a local cache to allow builds to be done from local caches

## Server

Pick a linux system with fast disk and network (not a Raspberry Pi) and install package:

```bash
sudo apt-get install -y apt-cacher-ng
```

You may also want to change the cache location, which is **/var/cache/apt-cacher-ng** by default.  To change the location, edit file /etc/ and change line:

```text
CacheDir: /var/cache/apt-cacher-ng
```

You also need to add line:

```text
PassThroughPattern: .*:443$
```

to allow https connections to pass through, otherwise they will fail to be served.  You cannot cache SSL repositories, as the cache cannot decrypt the SSL traffic, so simply needs to pass it through.

to specify an alternate location for the cache.  The location you choose must be a directory that is owned by user apt-cacher-ng.  E.g.

```bash
mkdir -p /mnt/ssd/apt-cache
sudo chown apt-cacher-ng:apt-cacher-ng /mnt/ssd/apt-cache
```

## Client

To make a Raspberry Pi use the local cache run the following command on the Raspberry Pi:

```bash
echo 'Acquire::http { proxy "http://YourCacheServerIP:3142"; };' | sudo tee /etc/apt/apt.conf.d/02proxy
```

replacing YourCacheServerIP with the IP address of your caching host.